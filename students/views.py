from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import (
    EducationForm, ExperienceForm, ProjectForm,
    ResumeUploadForm, StudentProfileForm
)
from .models import Education, Experience, Project, StudentProfile
from jobs.models import Job
from applications.models import Application
from ai_engine.resume_analyzer import analyze_resume
from ai_engine.recommender import get_recommended_jobs_for_student
from ai_engine.skill_gap import analyze_skill_gap, get_available_benchmark_roles


@login_required
def student_dashboard_view(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('role_redirect')

    profile = request.user.student_profile
    applications = Application.objects.filter(student=request.user).select_related('job', 'job__company')

    total_applications = applications.count()
    shortlisted_count = applications.filter(status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW, Application.STATUS_ACCEPTED]).count()
    under_review_count = applications.filter(status=Application.STATUS_REVIEWING).count()

    top_recommendations = get_recommended_jobs_for_student(profile, limit=4)

    context = {
        'profile': profile,
        'total_applications': total_applications,
        'shortlisted_count': shortlisted_count,
        'under_review_count': under_review_count,
        'recent_applications': applications.order_by('-applied_at')[:5],
        'top_recommendations': top_recommendations,
        'skills_list': profile.get_skills_list()[:8],
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def student_profile_view(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('role_redirect')

    profile = request.user.student_profile

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'educations': profile.educations.all(),
        'experiences': profile.experiences.all(),
        'projects': profile.projects.all(),
    }
    return render(request, 'student/profile.html', context)


@login_required
def student_resume_view(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('role_redirect')

    profile = request.user.student_profile

    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['resume_file']
            profile.resume_file = uploaded_file
            profile.save()

            # Execute AI Resume Analysis
            try:
                # Re-open file from storage
                with profile.resume_file.open('rb') as f:
                    insights = analyze_resume(f, profile.resume_file.name)

                profile.parsed_resume_text = insights['raw_text']
                profile.extracted_skills = insights['extracted_skills']
                profile.resume_sections = insights['sections']
                profile.ats_score = insights['ats_score']
                profile.ats_feedback = insights['ats_feedback']

                # Sync skills if empty
                if not profile.skills and insights['extracted_skills']:
                    profile.skills = ", ".join(insights['extracted_skills'])

                profile.save()
                messages.success(request, f"Resume parsed! ATS Score: {profile.ats_score}/100. Extracted {len(profile.extracted_skills)} skills.")
            except Exception as e:
                messages.warning(request, f"Resume saved, but AI parsing encountered an issue: {e}")

            return redirect('student_resume')
    else:
        form = ResumeUploadForm()

    context = {
        'profile': profile,
        'form': form,
        'skills': profile.extracted_skills,
        'ats_score': profile.ats_score,
        'ats_feedback': profile.ats_feedback,
        'sections': profile.resume_sections,
    }
    return render(request, 'student/resume.html', context)


@login_required
def student_recommendations_view(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('role_redirect')

    profile = request.user.student_profile
    recommendations = get_recommended_jobs_for_student(profile, limit=20)

    context = {
        'profile': profile,
        'recommendations': recommendations,
    }
    return render(request, 'student/recommendations.html', context)


@login_required
def student_skill_gap_view(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('role_redirect')

    profile = request.user.student_profile
    cand_skills = profile.get_skills_list()
    benchmark_roles = get_available_benchmark_roles()
    active_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).select_related('company')

    selected_mode = request.GET.get('mode', 'benchmark')  # 'benchmark' or 'job'
    target_id = request.GET.get('target', '')

    target_title = ""
    target_skills = []

    if selected_mode == 'job' and target_id:
        try:
            job = Job.objects.get(pk=int(target_id))
            target_title = f"{job.title} at {job.company.name}"
            target_skills = job.get_all_skills()
        except (Job.DoesNotExist, ValueError):
            pass

    if not target_skills and benchmark_roles:
        # Default to first benchmark role
        role_key = target_id if target_id in benchmark_roles else list(benchmark_roles.keys())[0]
        role_info = benchmark_roles[role_key]
        target_title = role_key
        target_skills = role_info['core_skills'] + role_info['recommended_skills']

    gap_analysis = analyze_skill_gap(cand_skills, target_skills, target_title)

    context = {
        'profile': profile,
        'cand_skills': cand_skills,
        'benchmark_roles': benchmark_roles,
        'active_jobs': active_jobs,
        'selected_mode': selected_mode,
        'selected_target': target_id,
        'gap_analysis': gap_analysis,
    }
    return render(request, 'student/skill_gap.html', context)


@login_required
def student_applications_view(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('role_redirect')

    applications = Application.objects.filter(student=request.user).select_related('job', 'job__company').order_by('-applied_at')

    context = {
        'applications': applications
    }
    return render(request, 'student/applications.html', context)
