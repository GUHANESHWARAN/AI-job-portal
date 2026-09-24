from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'First Name', 'autocomplete': 'given-name',
    }))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'Last Name', 'autocomplete': 'family-name',
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input', 'placeholder': 'you@example.com',
        'autocomplete': 'email', 'id': 'id_email',
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': '+91 98765 43210', 'autocomplete': 'tel',
    }))
    role = forms.ChoiceField(
        choices=(
            (User.ROLE_STUDENT, 'Student / Job Seeker'),
            (User.ROLE_RECRUITER, 'Recruiter / Employer')
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input', 'placeholder': 'e.g. john_doe123', 'autocomplete': 'username',
        })
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-input', 'placeholder': 'Min. 8 characters', 'autocomplete': 'new-password',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-input', 'placeholder': 'Repeat your password', 'autocomplete': 'new-password',
            })

    def clean_email(self):
        """Ensure each email address is used by exactly one account."""
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email address is already registered. "
                "Please sign in or use a different email."
            )
        return email


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'Username or Email',
        'autocomplete': 'username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': 'Password',
        'autocomplete': 'current-password',
    }))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Allow login by username OR email
            user = authenticate(username=username, password=password)
            if not user:
                try:
                    user_obj = User.objects.get(email__iexact=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                raise forms.ValidationError("Invalid username/email or password.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            cleaned_data['user'] = user

        return cleaned_data
