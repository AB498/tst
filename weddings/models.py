from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Wedding(models.Model):
    """Wedding model representing a wedding event"""
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('upcoming', 'Upcoming'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    bride_name = models.CharField(max_length=255)
    groom_name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administered_weddings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bride_name} & {self.groom_name} - {self.date}"

    @property
    def is_upcoming(self):
        return self.date > timezone.now().date()

    @property
    def is_today(self):
        return self.date == timezone.now().date()

    @property
    def is_past(self):
        return self.date < timezone.now().date()

class WeddingTeam(models.Model):
    """Team members assigned to a wedding"""
    ROLE_CHOICES = (
        ('coordinator', 'Wedding Coordinator'),
        ('photographer', 'Photographer'),
        ('videographer', 'Videographer'),
        ('florist', 'Florist'),
        ('caterer', 'Caterer'),
        ('dj', 'DJ/Music'),
        ('decorator', 'Decorator'),
        ('makeup_artist', 'Makeup Artist'),
        ('hair_stylist', 'Hair Stylist'),
        ('assistant', 'Assistant'),
        ('other', 'Other'),
    )

    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='team_members')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wedding_teams')
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wedding', 'member')

    def __str__(self):
        return f"{self.member.username} - {self.get_role_display()} for {self.wedding}"

class WeddingEvent(models.Model):
    """Individual events within a wedding (ceremony, reception, etc.)"""
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.wedding}"

    @property
    def is_upcoming(self):
        return self.date > timezone.now().date() or (self.date == timezone.now().date() and self.start_time > timezone.now().time())

class WeddingTheme(models.Model):
    """Wedding theme and style information"""
    wedding = models.OneToOneField(Wedding, on_delete=models.CASCADE, related_name='theme')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    color_scheme = models.CharField(max_length=255, blank=True, null=True)
    decoration_notes = models.TextField(blank=True, null=True)
    attire_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.wedding}"
