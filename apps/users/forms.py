from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User, StudentProfile, InstructorProfile


class StyledFormMixin:
    """Adds the Lodestar input styling class to every field automatically."""

    def _style(self):
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs['class'] = (existing + ' ls-checkbox').strip()
            else:
                field.widget.attrs['class'] = (existing + ' ls-input').strip()
            if field.help_text:
                field.widget.attrs['aria-describedby'] = f'{name}_help'


class RegistrationForm(StyledFormMixin, UserCreationForm):
    ROLE_CHOICES = (
        (User.Role.STUDENT, 'Student — I want to learn'),
        (User.Role.INSTRUCTOR, 'Instructor — I want to teach'),
    )

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial=User.Role.STUDENT)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['role'].widget.attrs.pop('class', None)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email


class StudentProfileForm(StyledFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = StudentProfile
        fields = [
            'profile_picture', 'bio', 'education', 'interests',
            'preferred_domains', 'current_level', 'learning_goals',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'learning_goals': forms.Textarea(attrs={'rows': 3}),
            'interests': forms.TextInput(attrs={'placeholder': 'e.g. Python, AI, Web Development'}),
            'preferred_domains': forms.TextInput(attrs={'placeholder': 'e.g. Data Science, Backend Development'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._style()
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['phone_number'].initial = self.user.phone_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.phone_number = self.cleaned_data['phone_number']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class InstructorProfileForm(StyledFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = InstructorProfile
        fields = ['profile_picture', 'bio', 'expertise', 'years_of_experience', 'linkedin_url']
        widgets = {'bio': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._style()
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['phone_number'].initial = self.user.phone_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.phone_number = self.cleaned_data['phone_number']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class LodestarAuthForm(StyledFormMixin, forms.Form):
    """Simple styled login form wrapper (kept separate from AuthenticationForm to control styling)."""
    username = forms.CharField(label='Username')
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
