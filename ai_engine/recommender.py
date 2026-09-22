"""
AI Recommender Engine:
Generates personalized job recommendations for students based on profile and resume matching,
and ranks candidate profiles for recruiters based on position criteria.
"""

from typing import Any, Dict, List, Optional
from django.db.models import QuerySet
from .matcher import compute_job_match


def get_recommended_jobs_for_student(
    student_profile: Any,
    limit: int = 12,
    min_score: float = 30.0
) -> List[Dict[str, Any]]:
    """
    Finds and ranks active jobs matching the student's skills, resume, and preferences.
    Excludes jobs the student has already applied to.
    """
    from jobs.models import Job
    from applications.models import Application

    applied_job_ids = Application.objects.filter(
        student=student_profile.user
    ).values_list('job_id', flat=True)

    active_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).exclude(id__in=applied_job_ids).select_related('company')

    candidate_skills = student_profile.get_skills_list()
    resume_text = student_profile.parsed_resume_text or student_profile.bio or " ".join(candidate_skills)

    recommendations = []

    for job in active_jobs:
        req_skills = job.required_skills if isinstance(job.required_skills, list) else []
        pref_skills = job.preferred_skills if isinstance(job.preferred_skills, list) else []
        job_text = f"{job.title} {job.description} {job.requirements} {job.responsibilities}"

        match_info = compute_job_match(
            candidate_skills=candidate_skills,
            resume_text=resume_text,
            job_required_skills=req_skills,
            job_preferred_skills=pref_skills,
            job_description=job_text,
            job_exp_level=job.experience_level,
            job_min_years=job.min_experience_years
        )

        if match_info['overall_score'] >= min_score:
            recommendations.append({
                'job': job,
                'match': match_info
            })

    # Sort descending by overall match score
    recommendations.sort(key=lambda x: x['match']['overall_score'], reverse=True)
    return recommendations[:limit]


def get_ranked_candidates_for_job(job: Any, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Ranks all students in the portal against a specific job's requirements for recruiter discovery.
    """
    from students.models import StudentProfile

    students = StudentProfile.objects.select_related('user').all()
    req_skills = job.required_skills if isinstance(job.required_skills, list) else []
    pref_skills = job.preferred_skills if isinstance(job.preferred_skills, list) else []
    job_text = f"{job.title} {job.description} {job.requirements} {job.responsibilities}"

    ranked = []
    for student in students:
        candidate_skills = student.get_skills_list()
        resume_text = student.parsed_resume_text or student.bio or " ".join(candidate_skills)

        match_info = compute_job_match(
            candidate_skills=candidate_skills,
            resume_text=resume_text,
            job_required_skills=req_skills,
            job_preferred_skills=pref_skills,
            job_description=job_text,
            job_exp_level=job.experience_level,
            job_min_years=job.min_experience_years
        )

        ranked.append({
            'student': student,
            'match': match_info
        })

    ranked.sort(key=lambda x: x['match']['overall_score'], reverse=True)
    return ranked[:limit]
