from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ls-input', 'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'class': 'ls-input', 'placeholder': 'you@example.com'}),
            'subject': forms.TextInput(attrs={'class': 'ls-input', 'placeholder': 'What is this about?'}),
            'message': forms.Textarea(attrs={'class': 'ls-input', 'rows': 5, 'placeholder': 'Tell us more...'}),
        }
