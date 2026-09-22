import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Job
from applications.models import Application
from ai_engine.matcher import compute_job_match
from ai_engine.jd_analyzer import analyze_job_description
from ai_engine.skill_extractor import extract_skills, extract_categorized_skills


def job_list_view(request):
    """
    Searchable, filterable list of all active opportunities with live AI match scoring.
    """
    query = request.GET.get('q', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()
    location = request.GET.get('location', '').strip()
    exp_level = request.GET.get('exp_level', '').strip()
    sort_by = request.GET.get('sort', 'newest')

    jobs_qs = Job.objects.filter(status=Job.STATUS_ACTIVE).select_related('company')

    if query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query) |
            Q(location__icontains=query)
        )

    if job_type:
        jobs_qs = jobs_qs.filter(job_type=job_type)
    if work_mode:
        jobs_qs = jobs_qs.filter(work_mode=work_mode)
    if location:
        jobs_qs = jobs_qs.filter(location__icontains=location)
    if exp_level:
        jobs_qs = jobs_qs.filter(experience_level=exp_level)

    # If student is logged in, attach AI match scores
    student_profile = None
    applied_job_ids = set()
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student_profile = request.user.student_profile
        applied_job_ids = set(
            Application.objects.filter(student=request.user).values_list('job_id', flat=True)
        )

    job_items = []
    cand_skills = student_profile.get_skills_list() if student_profile else []
    resume_text = (student_profile.parsed_resume_text or " ".join(cand_skills)) if student_profile else ""

    for job in jobs_qs:
        match_info = None
        if student_profile:
            match_info = compute_job_match(
                candidate_skills=cand_skills,
                resume_text=resume_text,
                job_required_skills=job.required_skills or [],
                job_preferred_skills=job.preferred_skills or [],
                job_description=f"{job.title} {job.description}",
                job_exp_level=job.experience_level,
                job_min_years=job.min_experience_years
            )
        job_items.append({
            'job': job,
            'match': match_info,
            'has_applied': job.id in applied_job_ids
        })

    # Sorting
    if sort_by == 'match' and student_profile:
        job_items.sort(key=lambda x: x['match']['overall_score'] if x['match'] else 0, reverse=True)
    elif sort_by == 'oldest':
        job_items.sort(key=lambda x: x['job'].created_at)
    else:  # newest
        job_items.sort(key=lambda x: x['job'].created_at, reverse=True)

    paginator = Paginator(job_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'job_type': job_type,
        'work_mode': work_mode,
        'location': location,
        'exp_level': exp_level,
        'sort_by': sort_by,
        'total_count': len(job_items),
        'is_internship_view': False
    }
    return render(request, 'student/jobs.html', context)


def internship_list_view(request):
    """Dedicated internship browsing portal."""
    query = request.GET.get('q', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()
    location = request.GET.get('location', '').strip()

    jobs_qs = Job.objects.filter(
        status=Job.STATUS_ACTIVE,
        job_type=Job.JOB_TYPE_INTERNSHIP
    ).select_related('company')

    if query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query)
        )
    if work_mode:
        jobs_qs = jobs_qs.filter(work_mode=work_mode)
    if location:
        jobs_qs = jobs_qs.filter(location__icontains=location)

    student_profile = None
    applied_job_ids = set()
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student_profile = request.user.student_profile
        applied_job_ids = set(
            Application.objects.filter(student=request.user).values_list('job_id', flat=True)
        )

    job_items = []
    cand_skills = student_profile.get_skills_list() if student_profile else []
    resume_text = (student_profile.parsed_resume_text or " ".join(cand_skills)) if student_profile else ""

    for job in jobs_qs:
        match_info = None
        if student_profile:
            match_info = compute_job_match(
                candidate_skills=cand_skills,
                resume_text=resume_text,
                job_required_skills=job.required_skills or [],
                job_preferred_skills=job.preferred_skills or [],
                job_description=f"{job.title} {job.description}",
                job_exp_level=job.experience_level,
                job_min_years=job.min_experience_years
            )
        job_items.append({
            'job': job,
            'match': match_info,
            'has_applied': job.id in applied_job_ids
        })

    job_items.sort(
        key=lambda x: (x['match']['overall_score'] if (student_profile and x['match']) else 0),
        reverse=True
    )

    paginator = Paginator(job_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'work_mode': work_mode,
        'location': location,
        'total_count': len(job_items),
        'is_internship_view': True
    }
    return render(request, 'student/internships.html', context)


def job_detail_view(request, pk):
    """
    Detailed job description, company overview, requirements,
    plus complete AI match breakdown and application button for students.
    """
    job = get_object_or_404(Job.objects.select_related('company', 'recruiter'), pk=pk)

    has_applied = False
    application = None
    match_info = None

    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student_profile = request.user.student_profile
        try:
            application = Application.objects.get(job=job, student=request.user)
            has_applied = True
            match_info = {
                'overall_score': application.overall_match_score,
                'skill_score': application.skill_match_score,
                'semantic_score': application.semantic_match_score,
                'experience_score': application.experience_match_score,
                **application.match_explanation
            }
        except Application.DoesNotExist:
            cand_skills = student_profile.get_skills_list()
            resume_text = student_profile.parsed_resume_text or " ".join(cand_skills)
            match_info = compute_job_match(
                candidate_skills=cand_skills,
                resume_text=resume_text,
                job_required_skills=job.required_skills or [],
                job_preferred_skills=job.preferred_skills or [],
                job_description=f"{job.title} {job.description} {job.requirements} {job.responsibilities}",
                job_exp_level=job.experience_level,
                job_min_years=job.min_experience_years
            )

    context = {
        'job': job,
        'has_applied': has_applied,
        'application': application,
        'match_info': match_info,
    }
    return render(request, 'job_detail.html', context)


@require_POST
def extract_skills_preview_api(request):
    """
    AJAX API: Extracts skills and analyzes description in real-time
    when a recruiter is typing a job posting.
    """
    try:
        data = json.loads(request.body)
        title = data.get('title', '')
        text = data.get('text', '')
        if not text:
            return JsonResponse({'success': False, 'error': 'No text provided.'})

        analysis = analyze_job_description(title=title, description=text)
        return JsonResponse({'success': True, 'data': analysis})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
