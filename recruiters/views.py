import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import RecruiterProfileForm
from .models import RecruiterProfile
from jobs.models import Job
from jobs.forms import JobForm
from applications.models import Application
from students.models import StudentProfile
from ai_engine.recommender import get_ranked_candidates_for_job
from ai_engine.matcher import compute_job_match


@login_required
def recruiter_dashboard_view(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    recruiter = request.user.recruiter_profile
    posted_jobs = Job.objects.filter(recruiter=request.user)
    active_jobs = posted_jobs.filter(status=Job.STATUS_ACTIVE)

    all_applications = Application.objects.filter(job__recruiter=request.user).select_related('student', 'job')
    total_applicants = all_applications.count()
    shortlisted_applicants = all_applications.filter(
        status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW, Application.STATUS_ACCEPTED]
    ).count()

    context = {
        'recruiter': recruiter,
        'total_jobs': posted_jobs.count(),
        'active_jobs_count': active_jobs.count(),
        'total_applicants': total_applicants,
        'shortlisted_applicants': shortlisted_applicants,
        'recent_applications': all_applications.order_by('-applied_at')[:8],
        'active_jobs': active_jobs[:5],
    }
    return render(request, 'recruiter/dashboard.html', context)


@login_required
def recruiter_profile_view(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    profile = request.user.recruiter_profile

    if request.method == 'POST':
        form = RecruiterProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Recruiter profile updated.")
            return redirect('recruiter_profile')
    else:
        form = RecruiterProfileForm(instance=profile)

    return render(request, 'recruiter/profile.html', {'form': form, 'profile': profile})


@login_required
def recruiter_create_job_view(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    profile = request.user.recruiter_profile
    if not profile.company:
        messages.warning(request, "Please attach a Company to your recruiter profile before posting jobs.")
        return redirect('recruiter_profile')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.company = profile.company
            job.required_skills = form.cleaned_data.get('required_skills', [])
            job.preferred_skills = form.cleaned_data.get('preferred_skills', [])
            job.save()
            messages.success(request, f"Opportunity '{job.title}' posted successfully!")
            return redirect('recruiter_manage_jobs')
    else:
        form = JobForm()

    return render(request, 'recruiter/create_job.html', {'form': form, 'company': profile.company})


@login_required
def recruiter_edit_job_view(request, pk):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    job = get_object_or_404(Job, pk=pk, recruiter=request.user)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.required_skills = form.cleaned_data.get('required_skills', [])
            job.preferred_skills = form.cleaned_data.get('preferred_skills', [])
            job.save()
            messages.success(request, f"Job '{job.title}' updated successfully.")
            return redirect('recruiter_manage_jobs')
    else:
        form = JobForm(instance=job)

    return render(request, 'recruiter/create_job.html', {'form': form, 'company': job.company, 'is_edit': True, 'job': job})


@login_required
def recruiter_manage_jobs_view(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    jobs = Job.objects.filter(recruiter=request.user).order_by('-created_at')

    # Status toggle action
    toggle_id = request.GET.get('toggle')
    if toggle_id:
        job = get_object_or_404(Job, pk=toggle_id, recruiter=request.user)
        job.status = Job.STATUS_CLOSED if job.status == Job.STATUS_ACTIVE else Job.STATUS_ACTIVE
        job.save()
        messages.info(request, f"Status for '{job.title}' updated to {job.get_status_display()}.")
        return redirect('recruiter_manage_jobs')

    context = {
        'jobs': jobs
    }
    return render(request, 'recruiter/manage_jobs.html', context)


@ensure_csrf_cookie
@login_required
def recruiter_applications_view(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    job_id = request.GET.get('job_id')
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', 'score')

    my_jobs = Job.objects.filter(recruiter=request.user)
    applications = Application.objects.filter(job__recruiter=request.user).select_related('student', 'student__student_profile', 'job')

    if job_id:
        applications = applications.filter(job_id=job_id)
    if status_filter:
        applications = applications.filter(status=status_filter)

    if sort_by == 'newest':
        applications = applications.order_by('-applied_at')
    else:  # 'score'
        applications = applications.order_by('-overall_match_score')

    context = {
        'my_jobs': my_jobs,
        'selected_job_id': job_id,
        'selected_status': status_filter,
        'sort_by': sort_by,
        'applications': applications,
        'status_choices': Application.STATUS_CHOICES,
    }
    return render(request, 'recruiter/applications.html', context)


@login_required
def recruiter_candidates_view(request):
    """
    AI Candidate Search & Discovery:
    Ranks talent across the platform against a selected job or custom skill criteria.
    """
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    my_jobs = Job.objects.filter(recruiter=request.user, status=Job.STATUS_ACTIVE)
    selected_job_id = request.GET.get('job_id')
    selected_job = None
    ranked_candidates = []

    if selected_job_id:
        try:
            selected_job = my_jobs.get(pk=selected_job_id)
            ranked_candidates = get_ranked_candidates_for_job(selected_job, limit=25)
        except Job.DoesNotExist:
            pass
    elif my_jobs.exists():
        selected_job = my_jobs.first()
        ranked_candidates = get_ranked_candidates_for_job(selected_job, limit=25)

    context = {
        'my_jobs': my_jobs,
        'selected_job': selected_job,
        'ranked_candidates': ranked_candidates,
    }
    return render(request, 'recruiter/candidates.html', context)


@ensure_csrf_cookie
@login_required
def recruiter_candidate_profile_view(request, user_id):
    """
    Candidate Dossier:
    Shows candidate details, ATS insights, resume, match breakdown against selected job.
    """
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('role_redirect')

    student_profile = get_object_or_404(StudentProfile.objects.select_related('user'), user_id=user_id)
    job_id = request.GET.get('job_id')
    job = None
    match_info = None
    application = None

    if job_id:
        try:
            job = Job.objects.get(pk=job_id, recruiter=request.user)
        except Job.DoesNotExist:
            job = None

    # Fallback: If no job_id or job not found, look up an application to any of this recruiter's jobs
    if not job:
        application = Application.objects.filter(
            job__recruiter=request.user,
            student=student_profile.user
        ).select_related('job').first()
        if application:
            job = application.job
    else:
        application = Application.objects.filter(job=job, student=student_profile.user).first()

    if job:
        cand_skills = student_profile.get_skills_list()
        resume_text = student_profile.parsed_resume_text or " ".join(cand_skills)
        match_info = compute_job_match(
            candidate_skills=cand_skills,
            resume_text=resume_text,
            job_required_skills=job.required_skills or [],
            job_preferred_skills=job.preferred_skills or [],
            job_description=f"{job.title} {job.description}",
            job_exp_level=job.experience_level,
            job_min_years=job.min_experience_years
        )

    context = {
        'student': student_profile,
        'job': job,
        'application': application,
        'match_info': match_info,
        'status_choices': Application.STATUS_CHOICES,
    }
    return render(request, 'recruiter/candidate_profile.html', context)


@require_POST
@login_required
def update_application_status_api(request, application_id):
    """
    AJAX endpoint for recruiters to update applicant pipeline status and notes.
    Triggers automated email notification to student when status changes.
    Enforces company/recruiter isolation strictly via job__recruiter=request.user.
    """
    if not hasattr(request.user, 'recruiter_profile'):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    app = get_object_or_404(Application, pk=application_id, job__recruiter=request.user)
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes')

        old_status = app.status
        status_changed = False

        if new_status and new_status in dict(Application.STATUS_CHOICES) and new_status != old_status:
            app.status = new_status
            status_changed = True

        if notes is not None:
            app.recruiter_notes = notes

        app.save()

        # Send automated email notification on status change (prevents duplicates)
        email_sent = False
        if status_changed:
            from applications.notifications import send_application_notification
            email_sent = send_application_notification(app, old_status=old_status, new_status=new_status)

        return JsonResponse({
            'success': True,
            'status': app.status,
            'status_display': app.get_status_display(),
            'email_sent': email_sent,
            'status_changed': status_changed,
            'student_email': app.student.email or '',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
