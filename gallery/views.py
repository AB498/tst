from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.urls import reverse

from .models import MediaCategory, Media, MediaComment, MediaLike, GalleryInvitation
from weddings.models import Wedding
from guests.models import Guest
from core.utils import send_gallery_invitation_email

@login_required
def wedding_list(request):
    """List all weddings the user has access to for gallery viewing"""
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
        # Guest sees weddings they're invited to
        guest_profiles = user.guest_profiles.all()
        weddings = [guest.wedding for guest in guest_profiles]
        weddings = Wedding.objects.filter(id__in=[w.id for w in weddings]).order_by('date')

    context = {'weddings': weddings}
    return render(request, 'gallery/wedding_list.html', context)

@login_required
def gallery_list(request):
    """List all media the user has access to"""
    user = request.user
    wedding_id = request.GET.get('wedding')

    # If no wedding_id is provided, redirect to wedding list
    if not wedding_id:
        return redirect('wedding_gallery_list')

    # Filter by wedding
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    if user.profile.role == 'admin' and wedding.admin != user:
        return HttpResponseForbidden("You don't have permission to view gallery for this wedding.")

    if user.profile.role == 'team_member' and not wedding.team_members.filter(member=user).exists():
        return HttpResponseForbidden("You don't have permission to view gallery for this wedding.")

    if user.profile.role == 'guest' and not user.guest_profiles.filter(wedding=wedding).exists():
        return HttpResponseForbidden("You don't have permission to view gallery for this wedding.")

    # Get media for this wedding
    media_items = Media.objects.filter(wedding=wedding, is_private=False).order_by('-upload_date')

    # If admin or team member, also show private media
    if user.profile.role in ['admin', 'team_member']:
        private_media = Media.objects.filter(wedding=wedding, is_private=True).order_by('-upload_date')
        media_items = list(media_items) + list(private_media)

    # Get categories for this wedding
    categories = MediaCategory.objects.filter(wedding=wedding)

    context = {
        'media_items': media_items,
        'categories': categories,
        'wedding': wedding
    }

    return render(request, 'gallery/gallery_list.html', context)

@login_required
def media_detail(request, media_id):
    """View media details"""
    media = get_object_or_404(Media, id=media_id)

    # Check if user has access to this media
    user = request.user
    has_access = False

    if user.profile.role == 'admin' and media.wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and media.wedding.team_members.filter(member=user).exists():
        has_access = True
    elif user.profile.role == 'guest' and user.guest_profiles.filter(wedding=media.wedding).exists():
        if not media.is_private:
            has_access = True

    if not has_access:
        return HttpResponseForbidden("You don't have permission to view this media.")

    # Get comments
    comments = media.comments.all().order_by('created_at')

    # Check if user has liked this media
    user_liked = media.likes.filter(user=user).exists()

    # Handle comment submission
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'comment':
            comment_text = request.POST.get('comment')

            if comment_text:
                MediaComment.objects.create(
                    media=media,
                    user=user,
                    comment=comment_text
                )

                messages.success(request, "Comment added successfully.")

        elif action == 'like':
            # Toggle like status
            if user_liked:
                media.likes.filter(user=user).delete()
                messages.success(request, "You unliked this media.")
                user_liked = False
            else:
                MediaLike.objects.create(
                    media=media,
                    user=user
                )
                messages.success(request, "You liked this media.")
                user_liked = True

        return redirect('media_detail', media_id=media.id)

    context = {
        'media': media,
        'comments': comments,
        'user_liked': user_liked,
    }

    return render(request, 'gallery/media_detail.html', context)

@login_required
def gallery_upload(request):
    """Upload media to gallery"""
    # Only admins, team members, and guests can upload media
    if request.user.profile.role not in ['admin', 'team_member', 'guest']:
        messages.error(request, "You don't have permission to upload media.")
        return redirect('dashboard')

    # Get wedding if provided in query params
    wedding_id = request.GET.get('wedding')
    if wedding_id:
        wedding = get_object_or_404(Wedding, id=wedding_id)

        # Check if user has access to this wedding
        if request.user.profile.role == 'admin' and wedding.admin != request.user:
            return HttpResponseForbidden("You don't have permission to upload media to this wedding.")

        if request.user.profile.role == 'team_member' and not wedding.team_members.filter(member=request.user).exists():
            return HttpResponseForbidden("You don't have permission to upload media to this wedding.")

        if request.user.profile.role == 'guest' and not request.user.guest_profiles.filter(wedding=wedding).exists():
            return HttpResponseForbidden("You don't have permission to upload media to this wedding.")
    else:
        wedding = None

    if request.method == 'POST':
        # Process form submission
        title = request.POST.get('title')
        description = request.POST.get('description')
        wedding_id = request.POST.get('wedding')
        category_id = request.POST.get('category')
        guest_id = request.POST.get('guest')
        media_type = request.POST.get('media_type')
        is_private = request.POST.get('is_private') == 'on'
        is_public = request.POST.get('is_public') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'

        if not title or not wedding_id or not media_type or 'file' not in request.FILES:
            messages.error(request, "Title, wedding, media type, and file are required fields.")
            return redirect('gallery_upload')

        wedding = get_object_or_404(Wedding, id=wedding_id)
        file = request.FILES['file']

        # Create media
        media = Media.objects.create(
            wedding=wedding,
            title=title,
            description=description,
            media_type=media_type,
            file=file,
            uploaded_by=request.user,
            is_private=is_private,
            is_public=is_public,
            is_featured=is_featured
        )

        # Set category if provided
        if category_id:
            media.category_id = category_id

        # Set guest if provided
        if guest_id:
            media.guest_id = guest_id

        # Save changes if category or guest was set
        if category_id or guest_id:
            media.save()

        messages.success(request, f"Media '{title}' uploaded successfully.")
        return redirect('media_detail', media_id=media.id)

    # Get available weddings based on user role
    if request.user.profile.role == 'admin':
        available_weddings = Wedding.objects.filter(admin=request.user)
    elif request.user.profile.role == 'team_member':
        wedding_teams = request.user.wedding_teams.all()
        available_weddings = [team.wedding for team in wedding_teams]
    else:
        guest_profiles = request.user.guest_profiles.all()
        available_weddings = [guest.wedding for guest in guest_profiles]

    # Get categories for the selected wedding
    categories = []
    guests = []
    if wedding:
        categories = MediaCategory.objects.filter(wedding=wedding)
        guests = wedding.guests.all().order_by('name')

    context = {
        'available_weddings': available_weddings,
        'selected_wedding': wedding,
        'categories': categories,
        'guests': guests,
    }

    return render(request, 'gallery/gallery_upload.html', context)

@login_required
def media_delete(request, media_id):
    """Delete media"""
    media = get_object_or_404(Media, id=media_id)

    # Check if user has permission
    if request.user.profile.role == 'admin' and media.wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to delete this media.")

    if request.user.profile.role == 'team_member' and not media.wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to delete this media.")

    if request.user.profile.role == 'guest' and request.user != media.uploaded_by:
        return HttpResponseForbidden("You don't have permission to delete this media.")

    if request.method == 'POST':
        wedding = media.wedding
        media_title = media.title
        media.delete()

        messages.success(request, f"Media '{media_title}' deleted successfully.")
        return redirect('gallery_list')

    context = {
        'media': media,
    }

    return render(request, 'gallery/media_confirm_delete.html', context)

@login_required
def wedding_gallery(request, wedding_id):
    """View gallery for a specific wedding"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    user = request.user
    has_access = False
    is_invited = False
    invitation_permission = None

    if user.profile.role == 'admin' and wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and wedding.team_members.filter(member=user).exists():
        has_access = True
    elif user.profile.role == 'guest' and user.guest_profiles.filter(wedding=wedding).exists():
        has_access = True

    # Check for gallery invitation
    invitation_token = request.session.get('gallery_invitation_token')
    if invitation_token:
        try:
            invitation = GalleryInvitation.objects.get(token=invitation_token, wedding=wedding)
            if invitation.is_accepted:
                has_access = True
                is_invited = True
                invitation_permission = invitation.permission
        except GalleryInvitation.DoesNotExist:
            # Invalid token, remove from session
            if 'gallery_invitation_token' in request.session:
                del request.session['gallery_invitation_token']

    if not has_access:
        # Check if gallery is public
        if Media.objects.filter(wedding=wedding, is_public=True).exists():
            return redirect('public_gallery', wedding_id=wedding.id)
        return HttpResponseForbidden("You don't have permission to view gallery for this wedding.")

    # Get media for this wedding
    media_items = Media.objects.filter(wedding=wedding, is_private=False).order_by('-upload_date')

    # If admin, team member, or invited with edit permission, also show private media
    if user.profile.role in ['admin', 'team_member'] or (is_invited and invitation_permission == 'edit'):
        private_media = Media.objects.filter(wedding=wedding, is_private=True).order_by('-upload_date')
        media_items = list(media_items) + list(private_media)

    # Get categories for this wedding
    categories = MediaCategory.objects.filter(wedding=wedding)

    context = {
        'media_items': media_items,
        'categories': categories,
        'wedding': wedding,
        'is_invited': is_invited,
        'invitation_permission': invitation_permission
    }

    return render(request, 'gallery/wedding_gallery.html', context)

@login_required
def guest_gallery(request, wedding_id, guest_id=None):
    """View gallery for a specific guest within a wedding"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if user has access to this wedding
    user = request.user
    has_access = False

    if user.profile.role == 'admin' and wedding.admin == user:
        has_access = True
    elif user.profile.role == 'team_member' and wedding.team_members.filter(member=user).exists():
        has_access = True
    elif user.profile.role == 'guest' and user.guest_profiles.filter(wedding=wedding).exists():
        has_access = True

    if not has_access:
        return HttpResponseForbidden("You don't have permission to view gallery for this wedding.")

    # Get all guests for this wedding
    guests = wedding.guests.all().order_by('name')

    # If guest_id is provided, filter media by that guest
    selected_guest = None
    if guest_id:
        selected_guest = get_object_or_404(wedding.guests, id=guest_id)
        media_items = Media.objects.filter(wedding=wedding, guest=selected_guest, is_private=False).order_by('-upload_date')

        # If admin or team member, also show private media
        if user.profile.role in ['admin', 'team_member']:
            private_media = Media.objects.filter(wedding=wedding, guest=selected_guest, is_private=True).order_by('-upload_date')
            media_items = list(media_items) + list(private_media)
    else:
        # Group media by guest
        media_by_guest = {}
        for guest in guests:
            guest_media = Media.objects.filter(wedding=wedding, guest=guest, is_private=False).order_by('-upload_date')

            # If admin or team member, also show private media
            if user.profile.role in ['admin', 'team_member']:
                private_media = Media.objects.filter(wedding=wedding, guest=guest, is_private=True).order_by('-upload_date')
                guest_media = list(guest_media) + list(private_media)

            if guest_media:
                media_by_guest[guest] = guest_media

        # Also get media not associated with any guest
        no_guest_media = Media.objects.filter(wedding=wedding, guest=None, is_private=False).order_by('-upload_date')

        # If admin or team member, also show private media
        if user.profile.role in ['admin', 'team_member']:
            private_no_guest_media = Media.objects.filter(wedding=wedding, guest=None, is_private=True).order_by('-upload_date')
            no_guest_media = list(no_guest_media) + list(private_no_guest_media)

        if no_guest_media:
            media_by_guest[None] = no_guest_media

        media_items = None

    context = {
        'wedding': wedding,
        'guests': guests,
        'selected_guest': selected_guest,
        'media_items': media_items,
        'media_by_guest': media_by_guest if not guest_id else None
    }

    return render(request, 'gallery/guest_gallery.html', context)

@login_required
def gallery_settings(request, wedding_id):
    """Manage gallery settings for a wedding"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Only admins and team members can manage gallery settings
    if request.user.profile.role == 'admin' and wedding.admin != request.user:
        return HttpResponseForbidden("You don't have permission to manage gallery settings for this wedding.")

    if request.user.profile.role == 'team_member' and not wedding.team_members.filter(member=request.user).exists():
        return HttpResponseForbidden("You don't have permission to manage gallery settings for this wedding.")

    if request.user.profile.role == 'guest':
        return HttpResponseForbidden("You don't have permission to manage gallery settings.")

    # Get all media for this wedding
    media_items = Media.objects.filter(wedding=wedding).order_by('-upload_date')

    # Get all invitations for this wedding
    invitations = GalleryInvitation.objects.filter(wedding=wedding).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_privacy':
            # Update privacy settings for all media
            is_public = request.POST.get('is_public') == 'on'

            # Update all media
            media_items.update(is_public=is_public)

            messages.success(request, "Gallery privacy settings updated successfully.")

        elif action == 'send_invitation':
            # Send invitation to view gallery
            email = request.POST.get('email')
            name = request.POST.get('name')
            permission = request.POST.get('permission')

            if not email or not permission:
                messages.error(request, "Email and permission are required.")
                return redirect('gallery_settings', wedding_id=wedding.id)

            # Check if invitation already exists
            existing_invitation = GalleryInvitation.objects.filter(wedding=wedding, email=email).first()
            if existing_invitation:
                # Update existing invitation
                existing_invitation.name = name
                existing_invitation.permission = permission
                existing_invitation.save()

                # Send invitation email
                email_sent = send_gallery_invitation_email(existing_invitation)

                if email_sent:
                    messages.success(request, f"Invitation updated and sent to {email}.")
                else:
                    messages.warning(request, f"Invitation updated but email could not be sent to {email}.")
            else:
                # Create new invitation
                invitation = GalleryInvitation.objects.create(
                    wedding=wedding,
                    email=email,
                    name=name,
                    permission=permission,
                    created_by=request.user
                )

                # Send invitation email
                email_sent = send_gallery_invitation_email(invitation)

                if email_sent:
                    messages.success(request, f"Invitation sent to {email}.")
                else:
                    messages.warning(request, f"Invitation created but email could not be sent to {email}.")

        elif action == 'delete_invitation':
            # Delete invitation
            invitation_id = request.POST.get('invitation_id')

            if not invitation_id:
                messages.error(request, "Invitation ID is required.")
                return redirect('gallery_settings', wedding_id=wedding.id)

            invitation = get_object_or_404(GalleryInvitation, id=invitation_id, wedding=wedding)
            email = invitation.email
            invitation.delete()

            messages.success(request, f"Invitation for {email} deleted successfully.")

    # Check if any media is public
    is_public = any(media.is_public for media in media_items)

    context = {
        'wedding': wedding,
        'media_items': media_items,
        'invitations': invitations,
        'is_public': is_public,
    }

    return render(request, 'gallery/gallery_settings.html', context)

def gallery_invite(request, token):
    """Handle gallery invitation access"""
    invitation = get_object_or_404(GalleryInvitation, token=token)
    wedding = invitation.wedding

    # Mark invitation as accepted
    if not invitation.is_accepted:
        invitation.accept()

    # If user is authenticated, grant them access
    if request.user.is_authenticated:
        # Check if user already has access
        if request.user.profile.role == 'admin' and wedding.admin == request.user:
            messages.info(request, "You already have admin access to this gallery.")
        elif request.user.profile.role == 'team_member' and wedding.team_members.filter(member=request.user).exists():
            messages.info(request, "You already have team member access to this gallery.")
        elif request.user.profile.role == 'guest' and request.user.guest_profiles.filter(wedding=wedding).exists():
            messages.info(request, "You already have guest access to this gallery.")
        else:
            # Grant temporary access by storing invitation token in session
            request.session['gallery_invitation_token'] = str(invitation.token)
            messages.success(request, f"You now have {dict(invitation.PERMISSION_CHOICES)[invitation.permission]} access to {wedding.title} gallery.")
    else:
        # Store invitation token in session and redirect to login
        request.session['gallery_invitation_token'] = str(invitation.token)
        messages.info(request, "Please log in or register to access the gallery.")
        return redirect(f"{reverse('login')}?next={reverse('wedding_gallery', args=[wedding.id])}")

    # Redirect to wedding gallery
    return redirect('wedding_gallery', wedding_id=wedding.id)

def public_gallery(request, wedding_id):
    """View public gallery for a wedding without login"""
    wedding = get_object_or_404(Wedding, id=wedding_id)

    # Check if any media is public
    public_media = Media.objects.filter(wedding=wedding, is_public=True).exists()

    if not public_media:
        messages.error(request, "This gallery is not publicly available.")
        return redirect('home')

    # Get all public media for this wedding
    media_items = Media.objects.filter(wedding=wedding, is_public=True).order_by('-upload_date')

    context = {
        'wedding': wedding,
        'media_items': media_items,
        'is_public_view': True,
    }

    return render(request, 'gallery/public_gallery.html', context)
