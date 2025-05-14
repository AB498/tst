from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

from weddings.models import Wedding, WeddingEvent

class Guest(models.Model):
    """Guest model for wedding attendees"""
    STATUS_CHOICES = (
        ('invited', 'Invited'),
        ('confirmed', 'Confirmed'),
        ('declined', 'Declined'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
    )

    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='guests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guest_profiles', null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    invitation_sent = models.BooleanField(default=False)
    invitation_sent_date = models.DateTimeField(blank=True, null=True)
    rsvp_date = models.DateTimeField(blank=True, null=True)
    check_in_date = models.DateTimeField(blank=True, null=True)
    plus_ones = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.wedding}"

    @property
    def is_checked_in(self):
        return self.status == 'attended'

    def check_in(self):
        self.status = 'attended'
        self.check_in_date = timezone.now()
        self.save()

class GuestCredential(models.Model):
    """Credentials for guest access"""
    guest = models.OneToOneField(Guest, on_delete=models.CASCADE, related_name='credential')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100, blank=True, null=True)  # Store plain password for email
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    expiry_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credentials for {self.guest.name}"

    def save(self, *args, **kwargs):
        # Generate QR code if it doesn't exist
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"http://localhost:8000/guests/qr/{self.token}/")
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")

            self.qr_code.save(f"qr_{self.guest.id}.png",
                             File(buffer), save=False)

        super().save(*args, **kwargs)

    def get_qr_code_base64(self):
        """Get QR code as base64 string for embedding in email"""
        import base64
        import os

        # If QR code doesn't exist, save to generate it
        if not self.qr_code:
            self.save()

        # Get the file path
        file_path = self.qr_code.path

        # Check if file exists
        if not os.path.exists(file_path):
            # Generate a new QR code on the fly
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"http://localhost:8000/guests/qr/{self.token}/")
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Convert to base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Read the file and convert to base64
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @property
    def is_valid(self):
        return timezone.now() < self.expiry_date

class Invitation(models.Model):
    """Virtual wedding invitation"""
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='invitations')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='invitations')
    message = models.TextField()
    sent_date = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)
    viewed_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Invitation for {self.guest.name} to {self.wedding}"

    def mark_as_viewed(self):
        self.viewed = True
        self.viewed_date = timezone.now()
        self.save()
