from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Wedding, WeddingTeam, WeddingEvent, WeddingTheme
from .forms import WeddingForm, WeddingEventForm, WeddingThemeForm, WeddingTeamForm, NewTeamMemberForm
from core.utils import create_team_member_user, send_team_member_invitation_email

@login_required
def wedding_list(request):
    """List all weddings the user has access to"""
    user = request.user

    # Check user role
    if user.profile.role == 'admin':
        # Admin sees all weddings they administer
        weddings = Wedding.objects.filter(admin=user).order_by('-date')
    elif user.profile.role == 'team_member':
        # Team member sees weddings they're assigned to
        wedding_teams = WeddingTeam.objects.filter(member=user)
        wedding_ids = [team.wedding.id for team in wedding_teams]
        weddings = Wedding.objects.filter(id__in=wedding_ids).order_by('-date')
    else:
        # Guest sees weddings they're invited to
        guest_profiles = user.guest_profiles.all()
        wedding_ids = [guest.wedding.id for guest in guest_profiles]
        weddings = Wedding.objects.filter(id__in=wedding_ids).order_by('-date')

    return render(request, 'weddings/wedding_list.html', {'weddings': weddings})

@login_required
def wedding_detail(request, wedding_id):
    """View wedding details"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    user = request.user
    has_access = False

    if user.profile.role == 'admin' and wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and WeddingTeam.objects.filter(wedding=wedding, member=user).exists():
        has_access = True
    elif user.profile.role == 'guest' and user.guest_profiles.filter(wedding=wedding).exists():
        has_access = True

    if not has_access:
        return HttpResponseForbidden("You don't have permission to view this wedding.")

    # Get wedding events
    events = WeddingEvent.objects.filter(wedding=wedding).order_by('date', 'start_time')

    # Get wedding team
    team = WeddingTeam.objects.filter(wedding=wedding)

    # Get wedding theme
    try:
        theme = WeddingTheme.objects.get(wedding=wedding)
    except WeddingTheme.DoesNotExist:
        theme = None

    # Get guest count
    guest_count = wedding.guests.count()
    confirmed_count = wedding.guests.filter(status='confirmed').count()
    attended_count = wedding.guests.filter(status='attended').count()

    context = {
        'wedding': wedding,
        'events': events,
        'team': team,
        'theme': theme,
        'guest_count': guest_count,
        'confirmed_count': confirmed_count,
        'attended_count': attended_count,
    }

    return render(request, 'weddings/wedding_detail.html', context)

@login_required
def wedding_create(request):
    """Create a new wedding"""
    # Only admins can create weddings
    if request.user.profile.role != 'admin':
        messages.error(request, "Only administrators can create weddings.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = WeddingForm(request.POST)
        if form.is_valid():
            wedding = form.save(commit=False)
            wedding.admin = request.user
            wedding.save()

            # Process tasks
            task_count = int(request.POST.get('task_count', 0))

            from tasks.models import Task

            for i in range(1, task_count + 1):
                task_title = request.POST.get(f'task_title_{i}')

                # Only create tasks with a title
                if task_title:
                    task_due_date = request.POST.get(f'task_due_date_{i}')
                    task_time = request.POST.get(f'task_time_{i}')
                    task_priority = request.POST.get(f'task_priority_{i}', 'medium')
                    task_description = request.POST.get(f'task_description_{i}')

                    # Create the task
                    Task.objects.create(
                        wedding=wedding,
                        title=task_title,
                        description=task_description,
                        due_date=task_due_date if task_due_date else wedding.date,
                        task_time=task_time if task_time else None,
                        priority=task_priority,
                        status='pending',
                        created_by=request.user
                    )

            messages.success(request, f"Wedding '{wedding.title}' created successfully.")
            return redirect('wedding_detail', wedding_id=wedding.id)
    else:
        form = WeddingForm()

    return render(request, 'weddings/wedding_form.html', {'form': form, 'action': 'Create'})

@login_required
def wedding_edit(request, wedding_id):
    """Edit an existing wedding"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Only the admin can edit the wedding
    if request.user != wedding.admin:
        messages.error(request, "You don't have permission to edit this wedding.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    if request.method == 'POST':
        form = WeddingForm(request.POST, instance=wedding)
        if form.is_valid():
            form.save()
            messages.success(request, f"Wedding '{wedding.title}' updated successfully.")
            return redirect('wedding_detail', wedding_id=wedding.id)
    else:
        form = WeddingForm(instance=wedding)

    return render(request, 'weddings/wedding_form.html', {'form': form, 'wedding': wedding, 'action': 'Edit'})

@login_required
def wedding_delete(request, wedding_id):
    """Delete a wedding"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Only the admin can delete the wedding
    if request.user != wedding.admin:
        messages.error(request, "You don't have permission to delete this wedding.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    if request.method == 'POST':
        wedding_title = wedding.title
        wedding.delete()
        messages.success(request, f"Wedding '{wedding_title}' deleted successfully.")
        return redirect('wedding_list')

    return render(request, 'weddings/wedding_confirm_delete.html', {'wedding': wedding})

@login_required
def wedding_team(request, wedding_id):
    """Manage wedding team members"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Only the admin can manage the team
    if request.user != wedding.admin:
        messages.error(request, "You don't have permission to manage this wedding's team.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    team_members = WeddingTeam.objects.filter(wedding=wedding)

    # Check if action is to remove a team member
    if request.method == 'POST' and request.POST.get('action') == 'remove':
        member_id = request.POST.get('member_id')
        if member_id:
            try:
                team_member = WeddingTeam.objects.get(id=member_id, wedding=wedding)
                username = team_member.member.username
                team_member.delete()
                messages.success(request, f"{username} removed from the team.")
            except WeddingTeam.DoesNotExist:
                messages.error(request, "Team member not found.")
        return redirect('wedding_team', wedding_id=wedding.id)

    # Check if action is to add an existing team member
    elif request.method == 'POST' and request.POST.get('action') == 'add':
        form = WeddingTeamForm(request.POST)
        if form.is_valid():
            team_member = form.save(commit=False)
            team_member.wedding = wedding

            # Check if this user is already on the team
            if WeddingTeam.objects.filter(wedding=wedding, member=team_member.member).exists():
                messages.error(request, f"{team_member.member.username} is already on the team.")
            else:
                team_member.save()
                messages.success(request, f"{team_member.member.username} added to the team as {form.cleaned_data['role']}.")

            return redirect('wedding_team', wedding_id=wedding.id)

    # Check if action is to create a new team member
    elif request.method == 'POST' and request.POST.get('action') == 'create':
        new_member_form = NewTeamMemberForm(request.POST)
        if new_member_form.is_valid():
            # Get form data
            first_name = new_member_form.cleaned_data['first_name']
            last_name = new_member_form.cleaned_data['last_name']
            email = new_member_form.cleaned_data['email']
            role = new_member_form.cleaned_data['role']

            # Create new user with team_member role
            user, password = create_team_member_user(email, first_name, last_name)

            if user:
                # Create team member
                team_member = WeddingTeam.objects.create(
                    wedding=wedding,
                    member=user,
                    role=role
                )

                # Send invitation email
                email_sent = send_team_member_invitation_email(user, password, wedding, dict(WeddingTeam.ROLE_CHOICES)[role])

                if email_sent:
                    messages.success(request, f"New team member {user.get_full_name()} created and added to the team as {dict(WeddingTeam.ROLE_CHOICES)[role]}. An invitation email has been sent.")
                else:
                    messages.warning(request, f"New team member {user.get_full_name()} created and added to the team, but the invitation email could not be sent.")
            else:
                messages.error(request, f"Could not create new team member. A user with email {email} may already exist.")

            return redirect('wedding_team', wedding_id=wedding.id)
    else:
        form = WeddingTeamForm()
        new_member_form = NewTeamMemberForm()

    # Check if there are any team members available
    available_team_members = User.objects.filter(profile__role='team_member').exists()

    context = {
        'wedding': wedding,
        'team_members': team_members,
        'form': form,
        'new_member_form': new_member_form,
        'available_team_members': available_team_members,
    }

    return render(request, 'weddings/wedding_team.html', context)

@login_required
def wedding_theme(request, wedding_id):
    """Manage wedding theme"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has permission
    if request.user != wedding.admin and not WeddingTeam.objects.filter(wedding=wedding, member=request.user).exists():
        messages.error(request, "You don't have permission to manage this wedding's theme.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    try:
        theme = WeddingTheme.objects.get(wedding=wedding)
    except WeddingTheme.DoesNotExist:
        theme = None

    if request.method == 'POST':
        if theme:
            form = WeddingThemeForm(request.POST, instance=theme)
        else:
            form = WeddingThemeForm(request.POST)

        if form.is_valid():
            theme = form.save(commit=False)
            theme.wedding = wedding
            theme.save()
            messages.success(request, "Wedding theme updated successfully.")
            return redirect('wedding_detail', wedding_id=wedding.id)
    else:
        if theme:
            form = WeddingThemeForm(instance=theme)
        else:
            form = WeddingThemeForm()

    context = {
        'wedding': wedding,
        'theme': theme,
        'form': form,
    }

    return render(request, 'weddings/wedding_theme.html', context)

@login_required
def wedding_event_create(request, wedding_id):
    """Create a new event for a wedding"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has permission
    user = request.user
    has_permission = False

    if user.profile.role == 'admin' and wedding.admin == user:
        has_permission = True
    elif user.profile.role == 'team_member' and WeddingTeam.objects.filter(wedding=wedding, member=user).exists():
        has_permission = True

    if not has_permission:
        messages.error(request, "You don't have permission to add events to this wedding.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    if request.method == 'POST':
        form = WeddingEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.wedding = wedding
            event.save()

            messages.success(request, f"Event '{event.name}' added successfully.")
            return redirect('wedding_detail', wedding_id=wedding.id)
    else:
        form = WeddingEventForm()

    context = {
        'form': form,
        'wedding': wedding,
    }

    return render(request, 'weddings/wedding_event_form.html', context)

@login_required
def wedding_event_edit(request, event_id):
    """Edit an existing wedding event"""
    event = get_object_or_404(WeddingEvent, id=event_id)
    wedding = event.wedding

    # Check if user has permission
    user = request.user
    has_permission = False

    if user.profile.role == 'admin' and wedding.admin == user:
        has_permission = True
    elif user.profile.role == 'team_member' and WeddingTeam.objects.filter(wedding=wedding, member=user).exists():
        has_permission = True

    if not has_permission:
        messages.error(request, "You don't have permission to edit this event.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    if request.method == 'POST':
        form = WeddingEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Event '{event.name}' updated successfully.")
            return redirect('wedding_detail', wedding_id=wedding.id)
    else:
        form = WeddingEventForm(instance=event)

    context = {
        'form': form,
        'wedding': wedding,
        'event': event,
    }

    return render(request, 'weddings/wedding_event_form.html', context)

@login_required
def wedding_event_delete(request, event_id):
    """Delete a wedding event"""
    event = get_object_or_404(WeddingEvent, id=event_id)
    wedding = event.wedding

    # Check if user has permission
    user = request.user
    has_permission = False

    if user.profile.role == 'admin' and wedding.admin == user:
        has_permission = True
    elif user.profile.role == 'team_member' and WeddingTeam.objects.filter(wedding=wedding, member=user).exists():
        has_permission = True

    if not has_permission:
        messages.error(request, "You don't have permission to delete this event.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    if request.method == 'POST':
        event_name = event.name
        event.delete()
        messages.success(request, f"Event '{event_name}' deleted successfully.")
        return redirect('wedding_detail', wedding_id=wedding.id)

    return render(request, 'weddings/wedding_event_confirm_delete.html', {'event': event})
