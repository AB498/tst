from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import UserProfile
from .forms import UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm
from weddings.models import Wedding, WeddingEvent
from tasks.models import Task
from guests.models import Guest

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Count some stats for the homepage
    stats = {
        'weddings': Wedding.objects.count(),
        'events': WeddingEvent.objects.count(),
        'guests': Guest.objects.count(),
    }

    return render(request, 'core/home.html', {'stats': stats})

@login_required
def dashboard(request):
    """Dashboard view based on user role"""
    user = request.user

    try:
        profile = user.profile
        role = profile.role
    except UserProfile.DoesNotExist:
        # Create a profile if it doesn't exist
        profile = UserProfile.objects.create(user=user, role='guest')
        role = 'guest'

    context = {
        'profile': profile,
    }

    # Admin dashboard
    if role == 'admin':
        # Get all weddings administered by this user
        weddings = Wedding.objects.filter(admin=user).order_by('-date')

        # Get upcoming events
        upcoming_events = WeddingEvent.objects.filter(
            wedding__admin=user,
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]

        # Get recent tasks
        recent_tasks = Task.objects.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).order_by('-created_at')[:5]

        # Get wedding stats
        wedding_stats = {
            'total': weddings.count(),
            'upcoming': weddings.filter(status='upcoming').count(),
            'in_progress': weddings.filter(status='in_progress').count(),
            'completed': weddings.filter(status='completed').count(),
        }

        context.update({
            'weddings': weddings,
            'upcoming_events': upcoming_events,
            'recent_tasks': recent_tasks,
            'wedding_stats': wedding_stats,
        })

        return render(request, 'core/dashboard_admin.html', context)

    # Team member dashboard
    elif role == 'team_member':
        # Get weddings where user is a team member
        wedding_teams = user.wedding_teams.all()
        weddings = [team.wedding for team in wedding_teams]

        # Get assigned tasks
        assigned_tasks = Task.objects.filter(assigned_to=user).order_by('-due_date')[:5]

        # Get upcoming events for these weddings
        upcoming_events = WeddingEvent.objects.filter(
            wedding__in=weddings,
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]

        context.update({
            'wedding_teams': wedding_teams,
            'weddings': weddings,
            'assigned_tasks': assigned_tasks,
            'upcoming_events': upcoming_events,
        })

        return render(request, 'core/dashboard_team.html', context)

    # Guest dashboard
    else:
        # Get guest profiles for this user
        guest_profiles = user.guest_profiles.all()

        # Get weddings for these guest profiles
        weddings = [guest.wedding for guest in guest_profiles]

        # Get upcoming events for these weddings
        upcoming_events = WeddingEvent.objects.filter(
            wedding__in=weddings,
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]

        context.update({
            'guest_profiles': guest_profiles,
            'weddings': weddings,
            'upcoming_events': upcoming_events,
        })

        return render(request, 'core/dashboard_guest.html', context)

def login_view(request):
    """Unified login view for all user types (admin, team members, and guests)"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # First try to authenticate as a regular user
        user = authenticate(username=username, password=password)

        if user is not None:
            # Regular user authentication successful
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('dashboard')
        else:
            # If regular authentication fails, try guest credentials
            try:
                from guests.models import GuestCredential
                # Find the guest credential with this username
                credential = GuestCredential.objects.get(username=username)

                # Check if credential is valid
                if not credential.is_valid:
                    messages.error(request, "Your login credentials have expired.")
                    return redirect('login')

                # Get the guest associated with this credential
                guest = credential.guest

                # Check if the password matches the stored plain text password
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
                    login(request, user)
                    messages.success(request, f"Welcome, {guest.name}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Invalid username or password.")
            except GuestCredential.DoesNotExist:
                # Neither regular user nor guest credential found
                messages.error(request, "Invalid username or password.")

    # For GET requests or failed authentication
    return render(request, 'auth/login.html', {'unified_login': True})

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a user profile
            UserProfile.objects.create(user=user, role='guest')
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}. You can now log in.")
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'auth/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view and update"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'active_tab': 'profile'
    }

    return render(request, 'core/profile.html', context)

@login_required
def settings(request):
    """User settings view and update"""
    if request.method == 'POST':
        password_form = CustomPasswordChangeForm(request.user, request.POST)

        if password_form.is_valid():
            user = password_form.save()
            # Update the session to prevent the user from being logged out
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated successfully.")
            return redirect('settings')
    else:
        password_form = CustomPasswordChangeForm(request.user)

    context = {
        'password_form': password_form,
        'active_tab': 'settings'
    }

    return render(request, 'core/settings.html', context)
