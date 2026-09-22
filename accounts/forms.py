from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input', 'placeholder': 'Email Address'
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'Phone Number'
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
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Username'})
        self.fields['password_1'] = self.fields.get('password_1')
        self.fields['password_2'] = self.fields.get('password_2')
        if 'password_1' in self.fields:
            self.fields['password_1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Password (min. 6 chars)'})
        if 'password_2' in self.fields:
            self.fields['password_2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirm Password'})


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input', 'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input', 'placeholder': 'Password'
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
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                raise forms.ValidationError("Invalid username/email or password.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            cleaned_data['user'] = user

        return cleaned_data
