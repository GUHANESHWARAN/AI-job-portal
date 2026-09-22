from django import forms
from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'website', 'industry', 'company_size', 'location', 'description', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Company Name'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://company.com'}),
            'industry': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Fintech, AI, Cloud'}),
            'company_size': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Bengaluru, India / San Francisco, CA'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'About the company...'}),
            'logo': forms.FileInput(attrs={'class': 'form-file-input', 'accept': 'image/*'}),
        }
