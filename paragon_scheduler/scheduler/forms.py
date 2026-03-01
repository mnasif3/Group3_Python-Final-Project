from django import forms
from .models import Client, Job


class ClientForm(forms.ModelForm):
    """Form for creating and editing clients."""
    
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number (optional)'
            }),
        }


class JobForm(forms.ModelForm):
    """Form for creating and editing jobs."""
    
    class Meta:
        model = Job
        fields = ['client', 'job_title', 'description', 'scheduled_date', 'note', 'type']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control',
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job description (optional)',
                'rows': 4
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add notes (optional)',
                'rows': 3
            }),
            'type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job type'
            }),
        }
