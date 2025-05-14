from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction

from .models import Task, TaskComment, Checklist, ChecklistItem, Reminder
from .forms import ChecklistForm, ChecklistItemFormSet
from weddings.models import Wedding

@login_required
def wedding_list(request):
    """List all weddings the user has access to for task management"""
    user = request.user

    # Get weddings based on user role
    if user.profile.role == 'admin':
        # Admin sees weddings they administer
        weddings = Wedding.objects.filter(admin=user).order_by('date')
    elif user.profile.role == 'team_member':
        # Team member sees weddings they're assigned to
        wedding_teams = user.wedding_teams.all()
        weddings = [team.wedding for team in wedding_teams]
        weddings = Wedding.objects.filter(id__in=[w.id for w in weddings]).order_by('date')
    else:
        # Guest doesn't see weddings for tasks
        weddings = []

    context = {'weddings': weddings}
    return render(request, 'tasks/wedding_list.html', context)

@login_required
def task_list(request):
    """List all tasks the user has access to"""
    user = request.user
    wedding_id = request.GET.get('wedding')

    # If no wedding_id is provided, redirect to wedding list
    if not wedding_id:
        return redirect('wedding_task_list')

    # Filter by wedding
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    if user.profile.role == 'admin' and wedding.admin != user:
        return HttpResponseForbidden("You don't have permission to view tasks for this wedding.")

    if user.profile.role == 'team_member' and not wedding.team_members.filter(member=user).exists():
        return HttpResponseForbidden("You don't have permission to view tasks for this wedding.")

    tasks = Task.objects.filter(wedding=wedding).order_by('-due_date')
    context = {'tasks': tasks, 'wedding': wedding}

    return render(request, 'tasks/task_list.html', context)

@login_required
def task_detail(request, task_id):
    """View task details"""
    task = get_object_or_404(Task, id=task_id)

    # Check if user has access to this task
    user = request.user
    has_access = False

    if user.profile.role == 'admin' and task.wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and task.wedding.team_members.filter(member=user).exists():
        has_access = True
    elif task.assigned_to == user:
        has_access = True

    if not has_access:
        return HttpResponseForbidden("You don't have permission to view this task.")

    # Get task comments
    comments = task.comments.all().order_by('created_at')

    # Handle comment submission
    if request.method == 'POST':
        comment_text = request.POST.get('comment')

        if comment_text:
            TaskComment.objects.create(
                task=task,
                user=user,
                comment=comment_text
            )

            messages.success(request, "Comment added successfully.")
            return redirect('task_detail', task_id=task.id)

    context = {
        'task': task,
        'comments': comments,
    }

    return render(request, 'tasks/task_detail.html', context)

@login_required
def task_create(request):
    """Create a new task"""
    # Only admins and team members can create tasks
    if request.user.profile.role not in ['admin', 'team_member']:
        messages.error(request, "You don't have permission to create tasks.")
        return redirect('dashboard')

    # Get wedding if provided in query params
    wedding_id = request.GET.get('wedding')
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if request.user.profile.role == 'admin' and wedding.admin != request.user:
            return HttpResponseForbidden("You don't have permission to add tasks to this wedding.")

        if request.user.profile.role == 'team_member' and not wedding.team_members.filter(member=request.user).exists():
            return HttpResponseForbidden("You don't have permission to add tasks to this wedding.")
    else:
        wedding = None

    if request.method == 'POST':
        # Process form submission
        title = request.POST.get('title')
        description = request.POST.get('description')
        wedding_id = request.POST.get('wedding')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        task_time = request.POST.get('task_time')
        priority = request.POST.get('priority')

        if not title or not wedding_id or not due_date:
            messages.error(request, "Title, wedding, and due date are required fields.")
            return redirect('task_create')

        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Create task
        task = Task.objects.create(
            wedding=wedding,
            title=title,
            description=description,
            assigned_to_id=assigned_to_id if assigned_to_id else None,
            created_by=request.user,
            due_date=due_date,
            task_time=task_time if task_time else None,
            priority=priority,
            status='pending'
        )

        messages.success(request, f"Task '{title}' created successfully.")
        return redirect('task_detail', task_id=task.id)

    # Get available weddings based on user role
    if request.user.profile.role == 'admin':
        available_weddings = Wedding.objects.filter(admin=request.user)
    else:
        wedding_teams = request.user.wedding_teams.all()
        available_weddings = [team.wedding for team in wedding_teams]

    context = {
        'available_weddings': available_weddings,
        'selected_wedding': wedding,
    }

    return render(request, 'tasks/task_form.html', context)

@login_required
def task_edit(request, task_id):
    """Edit an existing task"""
    task = get_object_or_404(Task, id=task_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and task.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to edit this task.")

    if request.user.profile.role == 'team_member' and not task.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to edit this task.")

    if request.user.profile.role == 'guest':
        return HttpResponseForbidden("You don't have permission to edit tasks.")

    if request.method == 'POST':
        # Process form submission
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.assigned_to_id = request.POST.get('assigned_to')
        task.due_date = request.POST.get('due_date')
        task.task_time = request.POST.get('task_time') if request.POST.get('task_time') else None
        task.priority = request.POST.get('priority')
        task.status = request.POST.get('status')

        task.save()

        messages.success(request, f"Task '{task.title}' updated successfully.")
        return redirect('task_detail', task_id=task.id)

    context = {
        'task': task,
    }

    return render(request, 'tasks/task_form.html', context)

@login_required
def task_delete(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and task.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to delete this task.")

    if request.user.profile.role == 'team_member' and not task.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to delete this task.")

    if request.user.profile.role == 'guest':
        return HttpResponseForbidden("You don't have permission to delete tasks.")

    if request.method == 'POST':
        task_title = task.title
        task.delete()

        messages.success(request, f"Task '{task_title}' deleted successfully.")
        return redirect('task_list')

    context = {
        'task': task,
    }

    return render(request, 'tasks/task_confirm_delete.html', context)

@login_required
def task_complete(request, task_id):
    """Mark a task as complete"""
    task = get_object_or_404(Task, id=task_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and task.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to complete this task.")

    if request.user.profile.role == 'team_member' and not task.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to complete this task.")

    if request.user.profile.role == 'guest':
        return HttpResponseForbidden("You don't have permission to complete tasks.")

    # Complete the task
    task.complete_task(request.user)

    messages.success(request, f"Task '{task.title}' marked as completed.")

    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', 'task_list'))

@login_required
def checklist(request):
    """View and manage checklists"""
    user = request.user
    wedding_id = request.GET.get('wedding')

    # Filter by wedding if provided
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if user.profile.role == 'admin' and wedding.admin != user:
            return HttpResponseForbidden("You don't have permission to view checklists for this wedding.")

        if user.profile.role == 'team_member' and not wedding.team_members.filter(member=user).exists():
            return HttpResponseForbidden("You don't have permission to view checklists for this wedding.")

        checklists = Checklist.objects.filter(wedding=wedding, is_template=False).order_by('title')
        context = {'checklists': checklists, 'wedding': wedding}
    else:
        # Show all checklists based on user role
        if user.profile.role == 'admin':
            # Admin sees checklists for weddings they administer and template checklists
            admin_weddings = Wedding.objects.filter(admin=user)
            checklists = Checklist.objects.filter(
                wedding__in=admin_weddings
            ).order_by('wedding', 'title')

            # Also show template checklists
            templates = Checklist.objects.filter(is_template=True).order_by('title')

            context = {'checklists': checklists, 'templates': templates}
        elif user.profile.role == 'team_member':
            # Team member sees checklists for weddings they're assigned to
            weddings = [team.wedding for team in user.wedding_teams.all()]
            checklists = Checklist.objects.filter(
                wedding__in=weddings
            ).order_by('wedding', 'title')

            context = {'checklists': checklists}
        else:
            # Guest doesn't see checklists
            context = {'checklists': []}

    return render(request, 'tasks/checklist.html', context)

@login_required
def reminders(request):
    """View and manage reminders"""
    user = request.user
    wedding_id = request.GET.get('wedding')

    # Filter by wedding if provided
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if user.profile.role == 'admin' and wedding.admin != user:
            return HttpResponseForbidden("You don't have permission to view reminders for this wedding.")

        if user.profile.role == 'team_member' and not wedding.team_members.filter(member=user).exists():
            return HttpResponseForbidden("You don't have permission to view reminders for this wedding.")

        reminders = Reminder.objects.filter(wedding=wedding).order_by('-reminder_date')
        context = {'reminders': reminders, 'wedding': wedding}
    else:
        # Show all reminders based on user role
        if user.profile.role == 'admin':
            # Admin sees reminders for weddings they administer
            admin_weddings = Wedding.objects.filter(admin=user)
            reminders = Reminder.objects.filter(
                wedding__in=admin_weddings
            ).order_by('wedding', '-reminder_date')

            context = {'reminders': reminders}
        elif user.profile.role == 'team_member':
            # Team member sees reminders for weddings they're assigned to
            weddings = [team.wedding for team in user.wedding_teams.all()]
            reminders = Reminder.objects.filter(
                wedding__in=weddings
            ).order_by('wedding', '-reminder_date')

            context = {'reminders': reminders}
        else:
            # Guest doesn't see reminders
            context = {'reminders': []}

    return render(request, 'tasks/reminders.html', context)

@login_required
def checklist_detail(request, checklist_id):
    """View checklist details"""
    checklist = get_object_or_404(Checklist, id=checklist_id)
    user = request.user

    # Check if user has access to this checklist
    has_access = False

    if checklist.is_template and user.profile.role == 'admin':
        has_access = True
    elif user.profile.role == 'admin' and checklist.wedding and checklist.wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and checklist.wedding and checklist.wedding.team_members.filter(member=user).exists():
        has_access = True

    if not has_access:
        return HttpResponseForbidden("You don't have permission to view this checklist.")

    # Get checklist items
    items = checklist.items.all().order_by('due_date', 'title')

    context = {
        'checklist': checklist,
        'items': items,
    }

    return render(request, 'tasks/checklist_detail.html', context)

@login_required
def checklist_create(request):
    """Create a new checklist"""
    # Only admins and team members can create checklists
    if request.user.profile.role not in ['admin', 'team_member']:
        messages.error(request, "You don't have permission to create checklists.")
        return redirect('dashboard')

    # Get wedding if provided in query params
    wedding_id = request.GET.get('wedding')
    wedding = None
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if request.user.profile.role == 'admin' and wedding.admin != request.user:
            return HttpResponseForbidden("You don't have permission to add checklists to this wedding.")

        if request.user.profile.role == 'team_member' and not wedding.team_members.filter(member=request.user).exists():
            return HttpResponseForbidden("You don't have permission to add checklists to this wedding.")

    if request.method == 'POST':
        form = ChecklistForm(request.POST, user=request.user)
        formset = ChecklistItemFormSet(request.POST)

        print(f"Form valid: {form.is_valid()}")
        print(f"Formset valid: {formset.is_valid()}")

        if not form.is_valid():
            print(f"Form errors: {form.errors}")

        if not formset.is_valid():
            print(f"Formset errors: {formset.errors}")

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save checklist
                    checklist = form.save(commit=False)
                    checklist.created_by = request.user

                    # If it's a template, set wedding to None
                    if checklist.is_template:
                        checklist.wedding = None

                    checklist.save()
                    print(f"Checklist saved: {checklist.id} - {checklist.title}")

                    # Save checklist items
                    formset.instance = checklist
                    formset.save()
                    print(f"Formset saved with {formset.total_form_count()} items")

                messages.success(request, f"Checklist '{checklist.title}' created successfully.")
            except Exception as e:
                print(f"Error saving checklist: {str(e)}")
                messages.error(request, f"Error creating checklist: {str(e)}")
            return redirect('checklist_detail', checklist_id=checklist.id)
    else:
        initial = {}
        if wedding:
            initial['wedding'] = wedding.id

        form = ChecklistForm(user=request.user, initial=initial)
        formset = ChecklistItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'selected_wedding': wedding,
    }

    return render(request, 'tasks/checklist_form.html', context)

@login_required
def checklist_edit(request, checklist_id):
    """Edit an existing checklist"""
    checklist = get_object_or_404(Checklist, id=checklist_id)
    user = request.user

    # Check if user has permission
    has_permission = False
    if checklist.is_template and user.profile.role == 'admin':
        has_permission = True
    elif user.profile.role == 'admin' and checklist.wedding and checklist.wedding.admin == user:
        has_permission = True
    elif user.profile.role == 'team_member' and checklist.wedding and checklist.wedding.team_members.filter(member=user).exists():
        has_permission = True

    if not has_permission:
        return HttpResponseForbidden("You don't have permission to edit this checklist.")

    if request.method == 'POST':
        form = ChecklistForm(request.POST, instance=checklist, user=request.user)
        formset = ChecklistItemFormSet(request.POST, instance=checklist)

        print(f"Edit form valid: {form.is_valid()}")
        print(f"Edit formset valid: {formset.is_valid()}")

        if not form.is_valid():
            print(f"Edit form errors: {form.errors}")

        if not formset.is_valid():
            print(f"Edit formset errors: {formset.errors}")

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save checklist
                    checklist = form.save()
                    print(f"Checklist updated: {checklist.id} - {checklist.title}")

                    # If it's a template, set wedding to None
                    if checklist.is_template:
                        checklist.wedding = None
                        checklist.save()
                        print("Set wedding to None for template")

                    # Save checklist items
                    formset.save()
                    print(f"Formset updated with {formset.total_form_count()} items")

                messages.success(request, f"Checklist '{checklist.title}' updated successfully.")
            except Exception as e:
                print(f"Error updating checklist: {str(e)}")
                messages.error(request, f"Error updating checklist: {str(e)}")
            return redirect('checklist_detail', checklist_id=checklist.id)
    else:
        form = ChecklistForm(instance=checklist, user=request.user)
        formset = ChecklistItemFormSet(instance=checklist)

    context = {
        'form': form,
        'formset': formset,
        'checklist': checklist,
    }

    return render(request, 'tasks/checklist_form.html', context)

@login_required
def checklist_delete(request, checklist_id):
    """Delete a checklist"""
    checklist = get_object_or_404(Checklist, id=checklist_id)
    user = request.user

    # Check if user has permission
    has_permission = False
    if checklist.is_template and user.profile.role == 'admin':
        has_permission = True
    elif user.profile.role == 'admin' and checklist.wedding and checklist.wedding.admin == user:
        has_permission = True
    elif user.profile.role == 'team_member' and checklist.wedding and checklist.wedding.team_members.filter(member=user).exists():
        has_permission = True

    if not has_permission:
        return HttpResponseForbidden("You don't have permission to delete this checklist.")

    if request.method == 'POST':
        checklist_title = checklist.title
        checklist.delete()

        messages.success(request, f"Checklist '{checklist_title}' deleted successfully.")
        return redirect('checklist')

    context = {
        'checklist': checklist,
    }

    return render(request, 'tasks/checklist_confirm_delete.html', context)

@login_required
def checklist_item_toggle(request, item_id):
    """Toggle a checklist item's completion status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        print(f"Processing toggle request for item ID: {item_id}")

        # Get the item
        try:
            item = ChecklistItem.objects.get(id=item_id)
            print(f"Found item: {item.id} - {item.title}")
        except ChecklistItem.DoesNotExist:
            print(f"Item with ID {item_id} not found")
            return JsonResponse({
                'status': 'error',
                'message': f"Item with ID {item_id} not found"
            }, status=404)

        user = request.user
        print(f"User: {user.username}, Role: {user.profile.role}")

        # Check if user has permission
        has_permission = False
        if item.checklist.is_template and user.profile.role == 'admin':
            has_permission = True
            print("Permission granted: Admin accessing template item")
        elif user.profile.role == 'admin' and item.checklist.wedding and item.checklist.wedding.admin == user:
            has_permission = True
            print("Permission granted: Admin accessing wedding item")
        elif user.profile.role == 'team_member' and item.checklist.wedding and item.checklist.wedding.team_members.filter(member=user).exists():
            has_permission = True
            print("Permission granted: Team member accessing wedding item")

        if not has_permission:
            print("Permission denied")
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

        # Toggle completion status
        current_status = item.is_completed
        print(f"Current completion status: {current_status}")

        if current_status:
            # Mark as incomplete
            print("Marking item as incomplete")
            item.is_completed = False
            item.completed_date = None
            item.completed_by = None
            item.save()

            print(f"Item {item.id} ({item.title}) marked as incomplete by {user.username}")

            return JsonResponse({
                'status': 'success',
                'is_completed': False,
                'message': f"Item '{item.title}' marked as incomplete."
            })
        else:
            # Mark as complete
            print("Marking item as complete")
            from django.utils import timezone
            item.is_completed = True
            item.completed_date = timezone.now()
            item.completed_by = user
            item.save()

            print(f"Item {item.id} ({item.title}) marked as complete by {user.username}")

            return JsonResponse({
                'status': 'success',
                'is_completed': True,
                'message': f"Item '{item.title}' marked as complete."
            })
    except Exception as e:
        import traceback
        print(f"Error in checklist_item_toggle: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }, status=500)

@login_required
def use_template(request, template_id):
    """Create a new checklist from a template"""
    template = get_object_or_404(Checklist, id=template_id, is_template=True)
    user = request.user

    # Only admins and team members can use templates
    if user.profile.role not in ['admin', 'team_member']:
        messages.error(request, "You don't have permission to use checklist templates.")
        return redirect('dashboard')

    # Get wedding if provided in query params
    wedding_id = request.GET.get('wedding')
    if not wedding_id:
        messages.error(request, "You must select a wedding to use this template.")
        return redirect('checklist')

    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    if user.profile.role == 'admin' and wedding.admin != user:
        return HttpResponseForbidden("You don't have permission to add checklists to this wedding.")

    if user.profile.role == 'team_member' and not wedding.team_members.filter(member=user).exists():
        return HttpResponseForbidden("You don't have permission to add checklists to this wedding.")

    if request.method == 'POST':
        # Create new checklist from template
        with transaction.atomic():
            new_checklist = Checklist.objects.create(
                title=template.title.replace('Template: ', ''),
                description=template.description,
                is_template=False,
                wedding=wedding,
                created_by=user
            )

            # Copy template items
            for item in template.items.all():
                ChecklistItem.objects.create(
                    checklist=new_checklist,
                    title=item.title,
                    description=item.description,
                    due_date=None,  # User will need to set due dates
                    is_completed=False
                )

        messages.success(request, f"Checklist '{new_checklist.title}' created from template successfully.")
        return redirect('checklist_detail', checklist_id=new_checklist.id)

    context = {
        'template': template,
        'wedding': wedding,
    }

    return render(request, 'tasks/use_template.html', context)
