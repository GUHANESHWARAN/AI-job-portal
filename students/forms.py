from django import forms
from .models import StudentProfile, Education, Experience, Project, Certification


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'readonly': 'readonly'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = StudentProfile
        fields = [
            'headline', 'bio', 'degree', 'institution', 'graduation_year', 'cgpa',
            'location', 'github_url', 'linkedin_url', 'portfolio_url', 'skills',
            'preferred_job_titles', 'preferred_locations', 'expected_salary'
        ]
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Full-Stack Python Developer | AI Enthusiast'}),
            'bio': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Brief professional summary...'}),
            'degree': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. B.Tech Computer Science & Engineering'}),
            'institution': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. National Institute of Technology'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2026'}),
            'cgpa': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '8.75'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City, State or Country'}),
            'github_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://github.com/username'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://linkedin.com/in/username'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://portfolio.dev'}),
            'skills': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Python, Django, MySQL, React, Docker'}),
            'preferred_job_titles': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Software Engineer, Backend Developer'}),
            'preferred_locations': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Bengaluru, Hyderabad, Remote'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Annual CTC in ₹ or $' }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
            profile.save()
        return profile


class ResumeUploadForm(forms.Form):
    resume_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-file-input', 'accept': '.pdf,.docx,.txt'}),
        help_text="Upload PDF, DOCX, or TXT (Max 5MB)"
    )


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_year', 'end_year', 'grade', 'description']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-input'}),
            'degree': forms.TextInput(attrs={'class': 'form-input'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-input'}),
            'start_year': forms.NumberInput(attrs={'class': 'form-input'}),
            'end_year': forms.NumberInput(attrs={'class': 'form-input'}),
            'grade': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
        }


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['title', 'company', 'location', 'start_date', 'end_date', 'is_current', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'company': forms.TextInput(attrs={'class': 'form-input'}),
            'location': forms.TextInput(attrs={'class': 'form-input'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'technologies', 'description', 'github_url', 'live_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'technologies': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Python, React, MySQL'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'github_url': forms.URLInput(attrs={'class': 'form-input'}),
            'live_url': forms.URLInput(attrs={'class': 'form-input'}),
        }
