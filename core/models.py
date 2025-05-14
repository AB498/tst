from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Extended user profile with additional fields"""
    USER_ROLES = (
        ('admin', 'Admin'),
        ('team_member', 'Team Member'),
        ('guest', 'Guest'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES, default='guest')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
