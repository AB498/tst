from django import forms
from django.contrib.auth.models import User
from django.core.validators import EmailValidator

from .models import Wedding, WeddingTeam, WeddingEvent, WeddingTheme

class WeddingForm(forms.ModelForm):
    """Form for creating and editing weddings"""
    class Meta:
        model = Wedding
        fields = ['title', 'description', 'bride_name', 'groom_name', 'date', 'time', 'location', 'address', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class WeddingEventForm(forms.ModelForm):
    """Form for creating and editing wedding events"""
    class Meta:
        model = WeddingEvent
        fields = ['name', 'description', 'date', 'start_time', 'end_time', 'location', 'address']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class WeddingThemeForm(forms.ModelForm):
    """Form for creating and editing wedding themes"""
    class Meta:
        model = WeddingTheme
        fields = ['name', 'description', 'color_scheme', 'decoration_notes', 'attire_notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'decoration_notes': forms.Textarea(attrs={'rows': 4}),
            'attire_notes': forms.Textarea(attrs={'rows': 4}),
        }

class WeddingTeamForm(forms.ModelForm):
    """Form for adding team members to a wedding"""
    # Define role choices directly in the form as a fallback
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

    # Override the role field to ensure it has choices
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = WeddingTeam
        fields = ['member', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users with team_member role
        self.fields['member'].queryset = User.objects.filter(profile__role='team_member')


class NewTeamMemberForm(forms.Form):
    """Form for creating a new team member user"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True, validators=[EmailValidator()])
    role = forms.ChoiceField(choices=WeddingTeamForm.ROLE_CHOICES, required=True)
