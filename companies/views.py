from django.shortcuts import render
from django.shortcuts import get_object_or_404, render
from .models import Company

# Create your views here.

def company_detail_view(request, slug):
    company = get_object_or_404(Company, slug=slug)
    jobs = company.jobs.filter(status='active').order_by('-created_at')
    return render(request, 'company_detail.html', {'company': company, 'jobs': jobs})
