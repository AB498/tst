from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.urls import reverse
import uuid
import datetime
import random
import string

from .models import Guest, GuestCredential, Invitation
from weddings.models import Wedding
from core.utils import send_guest_invitation_email

def generate_simple_password(length=8):
    """Generate a simple password for guests"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@login_required
def wedding_list(request):
    """List all weddings the user has access to for guest management"""
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
        # Guest doesn't see weddings for guest management
        weddings = []

    context = {'weddings': weddings}
    return render(request, 'guests/wedding_list.html', context)

@login_required
def guest_list(request):
    """List all guests the user has access to"""
    user = request.user
    wedding_id = request.GET.get('wedding')

    # If no wedding_id is provided, redirect to wedding list
    if not wedding_id:
        return redirect('wedding_guest_list')

    # Filter by wedding
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    if user.profile.role == 'admin' and wedding.admin != user:
        return HttpResponseForbidden("You don't have permission to view guests for this wedding.")

    if user.profile.role == 'team_member' and not wedding.team_members.filter(member=user).exists():
        return HttpResponseForbidden("You don't have permission to view guests for this wedding.")

    guests = Guest.objects.filter(wedding=wedding).order_by('name')
    context = {'guests': guests, 'wedding': wedding}

    return render(request, 'guests/guest_list.html', context)

@login_required
def guest_detail(request, guest_id):
    """View guest details"""
    guest = get_object_or_404(Guest, id=guest_id)

    # Check if user has access to this guest
    user = request.user
    has_access = False

    if user.profile.role == 'admin' and guest.wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and guest.wedding.team_members.filter(member=user).exists():
        has_access = True
    elif user == guest.user:
        has_access = True

    if not has_access:
        return HttpResponseForbidden("You don't have permission to view this guest.")

    # Get guest credential
    try:
        credential = guest.credential

        # Add a temporary password attribute if it doesn't exist in the database
        if not hasattr(credential, 'password') or credential.password is None:
            credential.temp_password = generate_simple_password()

    except GuestCredential.DoesNotExist:
        credential = None

    # Get invitations
    invitations = guest.invitations.all().order_by('-sent_date')

    context = {
        'guest': guest,
        'credential': credential,
        'invitations': invitations,
    }

    return render(request, 'guests/guest_detail.html', context)

@login_required
def guest_create(request):
    """Create a new guest"""
    # Only admins and team members can create guests
    if request.user.profile.role not in ['admin', 'team_member']:
        messages.error(request, "You don't have permission to create guests.")
        return redirect('dashboard')

    # Get wedding if provided in query params
    wedding_id = request.GET.get('wedding')
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if request.user.profile.role == 'admin' and wedding.admin != request.user:
            return HttpResponseForbidden("You don't have permission to add guests to this wedding.")

        if request.user.profile.role == 'team_member' and not wedding.team_members.filter(member=request.user).exists():
            return HttpResponseForbidden("You don't have permission to add guests to this wedding.")
    else:
        wedding = None

    if request.method == 'POST':
        # Process form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        plus_ones = request.POST.get('plus_ones', 0)
        notes = request.POST.get('notes')
        wedding_id = request.POST.get('wedding')

        if not name or not wedding_id:
            messages.error(request, "Name and wedding are required fields.")
            # Preserve the wedding parameter if it was in the original request
            original_wedding_id = request.GET.get('wedding')
            if original_wedding_id:
                create_url = f"{reverse('guest_create')}?wedding={original_wedding_id}"
                return redirect(create_url)
            else:
                return redirect('guest_create')

        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Create guest
        guest = Guest.objects.create(
            wedding=wedding,
            name=name,
            email=email,
            phone=phone,
            address=address,
            plus_ones=plus_ones,
            notes=notes,
            status='invited'
        )

        # Create credential
        expiry_date = wedding.date + datetime.timedelta(days=7)
        username = f"guest_{uuid.uuid4().hex[:8]}"
        password = generate_simple_password()

        GuestCredential.objects.create(
            guest=guest,
            username=username,
            password=password,
            expiry_date=expiry_date
        )

        messages.success(request, f"Guest '{name}' added successfully.")
        return redirect('guest_detail', guest_id=guest.id)

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

    return render(request, 'guests/guest_form.html', context)

@login_required
def guest_edit(request, guest_id):
    """Edit an existing guest"""
    guest = get_object_or_404(Guest, id=guest_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and guest.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to edit this guest.")

    if request.user.profile.role == 'team_member' and not guest.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to edit this guest.")

    if request.user.profile.role == 'guest':
        return HttpResponseForbidden("You don't have permission to edit guests.")

    if request.method == 'POST':
        # Process form submission
        guest.name = request.POST.get('name')
        guest.email = request.POST.get('email')
        guest.phone = request.POST.get('phone')
        guest.address = request.POST.get('address')
        guest.plus_ones = request.POST.get('plus_ones', 0)
        guest.notes = request.POST.get('notes')
        guest.status = request.POST.get('status')

        guest.save()

        messages.success(request, f"Guest '{guest.name}' updated successfully.")
        return redirect('guest_detail', guest_id=guest.id)

    context = {
        'guest': guest,
    }

    return render(request, 'guests/guest_form.html', context)

@login_required
def guest_delete(request, guest_id):
    """Delete a guest"""
    guest = get_object_or_404(Guest, id=guest_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and guest.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to delete this guest.")

    if request.user.profile.role == 'team_member' and not guest.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to delete this guest.")

    if request.user.profile.role == 'guest':
        return HttpResponseForbidden("You don't have permission to delete guests.")

    if request.method == 'POST':
        guest_name = guest.name
        guest.delete()

        messages.success(request, f"Guest '{guest_name}' deleted successfully.")
        return redirect('guest_list')

    context = {
        'guest': guest,
    }

    return render(request, 'guests/guest_confirm_delete.html', context)

def guest_login(request):
    """Handle guest login with username and password"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Find the guest credential with this username
            credential = GuestCredential.objects.get(username=username)

            # Check if credential is valid
            if not credential.is_valid:
                messages.error(request, "Your login credentials have expired.")
                return redirect('guest_login')

            # Get the guest associated with this credential
            guest = credential.guest

            # Check if the password matches the stored plain text password
            # This is for guest credentials that store plain text passwords
            if credential.password == password:
                # If guest already has a user, log them in
                if guest.user:
                    user = guest.user
                    # Update the user's password if it might have changed
                    user.set_password(password)
                    user.save()
                else:
                    # Create a new user for this guest
                    from django.contrib.auth.models import User
                    import uuid

                    # Create a unique username if needed
                    user_username = f"guest_{uuid.uuid4().hex[:8]}"

                    # Create the user
                    user = User.objects.create_user(
                        username=user_username,
                        password=password,  # This will hash the password
                        email=guest.email
                    )

                    # Set user profile to guest role
                    from core.models import UserProfile
                    UserProfile.objects.create(user=user, role='guest')

                    # Associate guest with user
                    guest.user = user
                    guest.save()

                # Log the user in
                from django.contrib.auth import login
                login(request, user)

                messages.success(request, f"Welcome, {guest.name}!")
                return redirect('dashboard')
            # If the guest already has a user account, try to authenticate with Django's system
            elif guest.user:
                from django.contrib.auth import authenticate, login
                user = authenticate(username=guest.user.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f"Welcome, {guest.name}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")
        except GuestCredential.DoesNotExist:
            messages.error(request, "Invalid username or password.")

    return render(request, 'guests/guest_login.html')

def guest_qr_login(request, token):
    """Handle QR code login"""
    try:
        credential = GuestCredential.objects.get(token=token)

        # Check if credential is valid
        if not credential.is_valid:
            messages.error(request, "This QR code has expired.")
            return redirect('home')

        # If user is already logged in, associate this guest with the user
        if request.user.is_authenticated and request.user.profile.role == 'guest':
            guest = credential.guest

            # Associate guest with user if not already associated
            if not guest.user:
                guest.user = request.user
                guest.save()
                messages.success(request, f"Welcome, {guest.name}! Your guest profile has been linked to your account.")

            return redirect('guest_detail', guest_id=guest.id)

        # Get the guest associated with this credential
        guest = credential.guest

        # If guest has a user account, log them in directly
        if guest.user:
            from django.contrib.auth import login
            login(request, guest.user)
            messages.success(request, f"Welcome, {guest.name}!")
            return redirect('dashboard')
        else:
            # Create a new user for this guest
            from django.contrib.auth.models import User
            import uuid

            # Create a unique username and use the credential password if available
            user_username = f"guest_{uuid.uuid4().hex[:8]}"
            password = credential.password or generate_simple_password()

            # Create the user
            user = User.objects.create_user(
                username=user_username,
                password=password,
                email=guest.email
            )

            # Set user profile to guest role
            from core.models import UserProfile
            UserProfile.objects.create(user=user, role='guest')

            # Associate guest with user
            guest.user = user
            guest.save()

            # Log the user in
            from django.contrib.auth import login
            login(request, user)

            messages.success(request, f"Welcome, {guest.name}!")
            return redirect('dashboard')

    except GuestCredential.DoesNotExist:
        messages.error(request, "Invalid QR code.")
        return redirect('home')

@login_required
def guest_checkin(request):
    """Check in a guest"""
    guest_id = request.GET.get('guest_id')

    if not guest_id:
        messages.error(request, "No guest specified.")
        return redirect('dashboard')

    guest = get_object_or_404(Guest, id=guest_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and guest.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to check in this guest.")

    if request.user.profile.role == 'team_member' and not guest.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to check in this guest.")

    if request.user.profile.role == 'guest' and request.user != guest.user:
        return HttpResponseForbidden("You don't have permission to check in this guest.")

    # Check in the guest
    guest.check_in()

    messages.success(request, f"{guest.name} has been checked in successfully.")

    # Redirect based on user role
    if request.user.profile.role == 'guest':
        return redirect('dashboard')
    else:
        return redirect('guest_detail', guest_id=guest.id)

@login_required
def send_invitation(request):
    """Send invitations to guests"""
    # Only admins and team members can send invitations
    if request.user.profile.role not in ['admin', 'team_member']:
        messages.error(request, "You don't have permission to send invitations.")
        return redirect('dashboard')

    # Get wedding if provided in query params
    wedding_id = request.GET.get('wedding')
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if request.user.profile.role == 'admin' and wedding.admin != request.user:
            return HttpResponseForbidden("You don't have permission to send invitations for this wedding.")

        if request.user.profile.role == 'team_member' and not wedding.team_members.filter(member=request.user).exists():
            return HttpResponseForbidden("You don't have permission to send invitations for this wedding.")

        # Get guests for this wedding who haven't been sent invitations
        guests = Guest.objects.filter(wedding=wedding, invitation_sent=False)
    else:
        # Get available weddings based on user role
        if request.user.profile.role == 'admin':
            available_weddings = Wedding.objects.filter(admin=request.user)
        else:
            wedding_teams = request.user.wedding_teams.all()
            available_weddings = [team.wedding for team in wedding_teams]

        guests = []
        wedding = None

    if request.method == 'POST':
        wedding_id = request.POST.get('wedding')
        guest_ids = request.POST.getlist('guests')
        message = request.POST.get('message')

        if not wedding_id or not guest_ids or not message:
            messages.error(request, "Wedding, guests, and message are required.")
            # Preserve the wedding parameter if it was in the original request
            original_wedding_id = request.GET.get('wedding')
            if original_wedding_id:
                return redirect(f"{reverse('send_invitation')}?wedding={original_wedding_id}")
            else:
                return redirect('send_invitation')

        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Send invitations to selected guests
        successful_invites = 0
        failed_invites = 0

        for guest_id in guest_ids:
            guest = get_object_or_404(Guest, id=guest_id)

            # Skip if guest has no email
            if not guest.email:
                messages.warning(request, f"No email address for {guest.name}. Invitation not sent.")
                continue

            # Get or create guest credential
            try:
                credential = guest.credential
            except GuestCredential.DoesNotExist:
                # Create credential if it doesn't exist
                expiry_date = wedding.date + datetime.timedelta(days=7)
                username = f"guest_{uuid.uuid4().hex[:8]}"
                password = generate_simple_password()
                credential = GuestCredential.objects.create(
                    guest=guest,
                    username=username,
                    password=password,
                    expiry_date=expiry_date
                )

            # Create invitation
            invitation = Invitation.objects.create(
                wedding=wedding,
                guest=guest,
                message=message
            )

            # Send email with invitation
            email_sent = send_guest_invitation_email(invitation, credential)

            if email_sent:
                # Update guest
                guest.invitation_sent = True
                guest.invitation_sent_date = timezone.now()
                guest.save()
                successful_invites += 1
            else:
                failed_invites += 1
                invitation.delete()  # Remove invitation if email failed

        # Show appropriate message based on results
        if successful_invites > 0 and failed_invites == 0:
            messages.success(request, f"Invitations successfully sent to {successful_invites} guests.")
        elif successful_invites > 0 and failed_invites > 0:
            messages.warning(request, f"Invitations sent to {successful_invites} guests. Failed to send to {failed_invites} guests.")
        else:
            messages.error(request, f"Failed to send invitations to {failed_invites} guests.")

        # Use query parameter instead of keyword argument
        return redirect(f"{reverse('guest_list')}?wedding={wedding_id}")

    context = {
        'guests': guests,
        'wedding': wedding,
        'available_weddings': available_weddings if not wedding else None,
    }

    return render(request, 'guests/send_invitation.html', context)
