"""
Utility functions for the Wedding Management System
"""
import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
import random
import string

def send_email(subject, to_email, template_name, context, attachments=None):
    """
    Send an email using a template

    Args:
        subject (str): Email subject
        to_email (str): Recipient email address
        template_name (str): Path to the HTML template
        context (dict): Context data for the template
        attachments (list): List of attachments (optional)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Render HTML content
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        # Debug information
        print(f"Sending email to: {to_email}")
        print(f"Subject: {subject}")

        # Create email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [to_email]
        )
        email.attach_alternative(html_content, "text/html")

        # Add attachments if any
        if attachments:
            for attachment in attachments:
                # Check if this is an inline attachment (for embedding in HTML)
                if attachment.get('inline', False):
                    # Add as MIMEImage with Content-ID
                    from email.mime.image import MIMEImage
                    image = MIMEImage(attachment['content'])
                    image.add_header('Content-ID', f'<{attachment["name"]}>')
                    image.add_header('Content-Disposition', 'inline', filename=attachment['name'])
                    email.attach(image)
                else:
                    # Add as regular attachment
                    email.attach(attachment['name'], attachment['content'], attachment['type'])

        # Send email
        email.send()
        print(f"Email sent successfully to {to_email}!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_guest_invitation_email(invitation, credential):
    """
    Send an invitation email to a guest with their login credentials

    Args:
        invitation: Invitation object
        credential: GuestCredential object

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    guest = invitation.guest
    wedding = invitation.wedding

    # Skip if guest has no email
    if not guest.email:
        return False

    # Generate a temporary password if the credential doesn't have one
    password = credential.password if hasattr(credential, 'password') else generate_random_password(8)

    # Get the base URL from settings or use localhost as fallback
    from django.conf import settings

    # Determine the base URL based on environment
    if settings.ON_RAILWAY:
        # Use the Railway-provided URL if available
        base_url = f"https://{settings.ALLOWED_HOSTS[0]}" if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS[0] != '*' else "https://your-app-name.up.railway.app"
    else:
        # Use localhost for development
        base_url = "http://localhost:8000"

    # Prepare context for email template
    context = {
        'guest': guest,
        'wedding': wedding,
        'invitation': invitation,
        'credential': credential,
        'qr_code_base64': credential.get_qr_code_base64(),
        'login_url': f"{base_url}/guests/qr/{credential.token}/",
        'direct_login_url': f"{base_url}/guests/login/",
        'username': credential.username,
        'password': password,
    }

    # Prepare QR code as attachment
    from io import BytesIO

    # Get QR code image
    if credential.qr_code and hasattr(credential.qr_code, 'path') and os.path.exists(credential.qr_code.path):
        # Use existing QR code file
        with open(credential.qr_code.path, 'rb') as f:
            qr_content = f.read()
    else:
        # Generate QR code on the fly
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"http://localhost:8000/guests/qr/{credential.token}/")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_content = buffer.getvalue()

    # Create attachment
    attachments = [{
        'name': 'qr_code.png',
        'content': qr_content,
        'type': 'image/png',
        'inline': True  # Mark as inline for embedding in HTML
    }]

    # Send email
    subject = f"You're invited to {wedding.bride_name} & {wedding.groom_name}'s Wedding"
    return send_email(subject, guest.email, 'emails/guest_invitation.html', context, attachments=attachments)

def generate_random_password(length=10):
    """
    Generate a random password

    Args:
        length (int): Length of the password

    Returns:
        str: Random password
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def create_team_member_user(email, first_name, last_name):
    """
    Create a new user with team_member role

    Args:
        email (str): Email address
        first_name (str): First name
        last_name (str): Last name

    Returns:
        tuple: (User object, password) if created successfully, (None, None) otherwise
    """
    try:
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return None, None

        # Generate username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1

        # Make sure username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Generate random password
        password = generate_random_password()

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Set user profile role to team_member
        user.profile.role = 'team_member'
        user.profile.save()

        return user, password
    except Exception as e:
        print(f"Error creating team member user: {e}")
        return None, None

def send_team_member_invitation_email(user, password, wedding, role):
    """
    Send an invitation email to a new team member with their login credentials

    Args:
        user: User object
        password: Generated password
        wedding: Wedding object
        role: Team member role

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Skip if user has no email
    if not user.email:
        return False

    # Get the base URL from settings or use localhost as fallback
    from django.conf import settings

    # Determine the base URL based on environment
    if settings.ON_RAILWAY:
        # Use the Railway-provided URL if available
        base_url = f"https://{settings.ALLOWED_HOSTS[0]}" if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS[0] != '*' else "https://your-app-name.up.railway.app"
    else:
        # Use localhost for development
        base_url = "http://localhost:8000"

    # Prepare context for email template
    context = {
        'user': user,
        'password': password,
        'wedding': wedding,
        'role': role,
        'login_url': f'{base_url}/login/',
    }

    # Send email
    subject = f"You've been added to the {wedding.bride_name} & {wedding.groom_name}'s Wedding Team"
    return send_email(subject, user.email, 'emails/team_member_invitation.html', context)

def send_gallery_invitation_email(invitation):
    """
    Send an invitation email for gallery access

    Args:
        invitation: GalleryInvitation object

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Skip if no email
    if not invitation.email:
        return False

    # Get the base URL from settings or use localhost as fallback
    from django.conf import settings

    # Determine the base URL based on environment
    if settings.ON_RAILWAY:
        # Use the Railway-provided URL if available
        base_url = f"https://{settings.ALLOWED_HOSTS[0]}" if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS[0] != '*' else "https://your-app-name.up.railway.app"
    else:
        # Use localhost for development
        base_url = "http://localhost:8000"

    # Prepare context for email template
    context = {
        'invitation': invitation,
        'wedding': invitation.wedding,
        'permission': dict(invitation.PERMISSION_CHOICES)[invitation.permission],
        'access_url': f"{base_url}/gallery/invite/{invitation.token}/",
    }

    # Send email
    subject = f"You've been invited to view {invitation.wedding.bride_name} & {invitation.wedding.groom_name}'s Wedding Gallery"
    return send_email(subject, invitation.email, 'emails/gallery_invitation.html', context)
