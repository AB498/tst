from django import forms
from django.forms import inlineformset_factory
from .models import Checklist, ChecklistItem

class ChecklistForm(forms.ModelForm):
    """Form for creating and editing checklists"""
    class Meta:
        model = Checklist
        fields = ['title', 'description', 'is_template', 'wedding']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50', 'rows': 3}),
            'is_template': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'wedding': forms.Select(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Make wedding not required initially, we'll validate in clean()
        self.fields['wedding'].required = False

        if user:
            # If user is admin, show all weddings they administer
            if user.profile.role == 'admin':
                self.fields['wedding'].queryset = user.administered_weddings.all()
            # If user is team member, show all weddings they're part of
            elif user.profile.role == 'team_member':
                from weddings.models import Wedding
                wedding_ids = user.wedding_teams.values_list('wedding_id', flat=True)
                self.fields['wedding'].queryset = Wedding.objects.filter(id__in=wedding_ids)

            # If creating a template, hide the wedding field
            if self.instance and self.instance.is_template:
                self.fields['wedding'].widget = forms.HiddenInput()

            # If the form data indicates this is a template
            if self.data.get('is_template') == 'on':
                self.fields['wedding'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        is_template = cleaned_data.get('is_template')
        wedding = cleaned_data.get('wedding')

        # If it's a template, wedding should be None
        if is_template:
            cleaned_data['wedding'] = None
        # If it's not a template, wedding is required
        elif not wedding:
            self.add_error('wedding', 'Wedding is required for non-template checklists.')

        return cleaned_data

class ChecklistItemForm(forms.ModelForm):
    """Form for creating and editing checklist items"""
    class Meta:
        model = ChecklistItem
        fields = ['title', 'description', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50', 'rows': 2}),
            'due_date': forms.DateInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50', 'type': 'date'}),
        }

# Create a formset for checklist items
ChecklistItemFormSet = inlineformset_factory(
    Checklist,
    ChecklistItem,
    form=ChecklistItemForm,
    extra=3,
    can_delete=True
)
