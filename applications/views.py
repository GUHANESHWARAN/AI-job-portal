from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Application
from jobs.models import Job
from ai_engine.matcher import compute_job_match


@login_required
def apply_job_view(request, job_id):
    """
    Submits application for a job.
    Calculates and captures AI Match snapshot at the moment of submission.
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only student accounts can apply for positions.")
        return redirect('job_detail', pk=job_id)

    job = get_object_or_404(Job, pk=job_id, status=Job.STATUS_ACTIVE)
    profile = request.user.student_profile

    # Check existing application
    if Application.objects.filter(job=job, student=request.user).exists():
        messages.warning(request, "You have already applied for this position.")
        return redirect('job_detail', pk=job_id)

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '').strip()
        custom_resume = request.FILES.get('resume_file')

        # Use profile resume or custom resume
        resume_file_to_use = custom_resume or profile.resume_file

        cand_skills = profile.get_skills_list()
        resume_text = profile.parsed_resume_text or " ".join(cand_skills)

        # Run AI matching calculation
        match_info = compute_job_match(
            candidate_skills=cand_skills,
            resume_text=resume_text,
            job_required_skills=job.required_skills or [],
            job_preferred_skills=job.preferred_skills or [],
            job_description=f"{job.title} {job.description} {job.requirements} {job.responsibilities}",
            job_exp_level=job.experience_level,
            job_min_years=job.min_experience_years
        )

        app = Application.objects.create(
            job=job,
            student=request.user,
            cover_letter=cover_letter,
            resume_file=resume_file_to_use,
            overall_match_score=match_info['overall_score'],
            skill_match_score=match_info['skill_score'],
            semantic_match_score=match_info['semantic_score'],
            experience_match_score=match_info['experience_score'],
            match_explanation=match_info,
            status=Application.STATUS_APPLIED
        )

        # Send application submission confirmation email
        from applications.notifications import send_application_notification
        send_application_notification(app, old_status='', new_status=Application.STATUS_APPLIED)

        messages.success(
            request,
            f"Successfully applied to {job.title}! Your AI match score is {app.overall_match_score:.1f}%."
        )
        return redirect('student_applications')

    # GET request shows application confirmation page
    cand_skills = profile.get_skills_list()
    resume_text = profile.parsed_resume_text or " ".join(cand_skills)
    match_info = compute_job_match(
        candidate_skills=cand_skills,
        resume_text=resume_text,
        job_required_skills=job.required_skills or [],
        job_preferred_skills=job.preferred_skills or [],
        job_description=f"{job.title} {job.description} {job.requirements}",
        job_exp_level=job.experience_level,
        job_min_years=job.min_experience_years
    )

    context = {
        'job': job,
        'profile': profile,
        'match_info': match_info
    }
    return render(request, 'apply_confirm.html', context)


@login_required
def withdraw_application_view(request, application_id):
    app = get_object_or_404(Application, pk=application_id, student=request.user)
    job_title = app.job.title
    app.delete()
    messages.info(request, f"Your application for {job_title} has been withdrawn.")
    return redirect('student_applications')
