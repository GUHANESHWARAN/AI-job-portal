from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    required_skills_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'id': 'required_skills_input',
            'placeholder': 'e.g. Python, Django, MySQL, Docker (comma separated)'
        }),
        help_text="Comma-separated mandatory skills (or use AI extractor below)"
    )
    preferred_skills_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'id': 'preferred_skills_input',
            'placeholder': 'e.g. AWS, Redis, React, Celery'
        }),
        help_text="Comma-separated nice-to-have skills"
    )

    class Meta:
        model = Job
        fields = [
            'title', 'job_type', 'work_mode', 'location', 'experience_level',
            'min_experience_years', 'salary_min', 'salary_max', 'is_salary_negotiable',
            'description', 'responsibilities', 'requirements', 'deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Senior Backend Engineer'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'work_mode': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Bengaluru, India or Remote'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'min_experience_years': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Min Salary / Stipend (₹ or $)'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Max Salary / Stipend'}),
            'is_salary_negotiable': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'id': 'job_description', 'rows': 6, 'placeholder': 'Enter comprehensive job description...'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Key daily responsibilities...'}),
            'requirements': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Prerequisites & qualifications...'}),
            'deadline': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if isinstance(self.instance.required_skills, list):
                self.fields['required_skills_input'].initial = ", ".join(self.instance.required_skills)
            if isinstance(self.instance.preferred_skills, list):
                self.fields['preferred_skills_input'].initial = ", ".join(self.instance.preferred_skills)

    def clean(self):
        cleaned_data = super().clean()
        req_str = cleaned_data.get('required_skills_input', '')
        pref_str = cleaned_data.get('preferred_skills_input', '')

        cleaned_data['required_skills'] = [s.strip() for s in req_str.split(',') if s.strip()]
        cleaned_data['preferred_skills'] = [s.strip() for s in pref_str.split(',') if s.strip()]
        return cleaned_data

