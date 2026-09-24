from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import JsonResponse
from .forms import UserLoginForm, UserRegistrationForm
from .models import User

# Create your views here.

def register_view(request):
    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CareerAI, {user.first_name or user.username}! Your account has been created.")
            return redirect('role_redirect')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        initial_role = request.GET.get('role', User.ROLE_STUDENT)
        form = UserRegistrationForm(initial={'role': initial_role})

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('role_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')


@login_required
def role_redirect_view(request):
    user = request.user
    if user.is_superuser or user.role == User.ROLE_ADMIN:
        return redirect('admin_dashboard')
    elif user.role == User.ROLE_RECRUITER:
        return redirect('recruiter_dashboard')
    else:
        return redirect('student_dashboard')


def home_view(request):
    from jobs.models import Job
    from companies.models import Company
    from students.models import StudentProfile

    featured_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).select_related('company')[:6]
    total_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE, job_type=Job.JOB_TYPE_FULL_TIME).count()
    total_internships = Job.objects.filter(status=Job.STATUS_ACTIVE, job_type=Job.JOB_TYPE_INTERNSHIP).count()
    total_companies = Company.objects.count()
    total_candidates = StudentProfile.objects.count()

    context = {
        'featured_jobs': featured_jobs,
        'total_jobs': total_jobs,
        'total_internships': total_internships,
        'total_companies': total_companies,
        'total_candidates': total_candidates,
    }
    return render(request, 'home.html', context)


def check_email_view(request):
    """AJAX endpoint — returns JSON {available: bool} for real-time email uniqueness check."""
    email = request.GET.get('email', '').strip().lower()
    if not email:
        return JsonResponse({'available': False, 'error': 'No email provided'})
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'available': not exists})
