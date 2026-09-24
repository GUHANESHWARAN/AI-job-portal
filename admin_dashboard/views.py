import calendar
import csv
from collections import Counter
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from applications.models import Application
from companies.models import Company
from jobs.models import Job
from recruiters.models import RecruiterProfile
from students.models import Certification, Education, Experience, StudentProfile


def admin_required(view_func):
    """
    Server-side role authorization decorator.
    Only allows superusers or users with role == 'admin'.
    Denies students and recruiters, redirecting unauthenticated users to login
    and non-admin users to home.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_superuser or request.user.role == User.ROLE_ADMIN):
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return _wrapped


def build_monthly_trend(queryset, date_field='created_at', days=180):
    """
    Database-agnostic monthly trend calculation.
    Groups datetimes in Python to ensure compatibility across MySQL, PostgreSQL, and SQLite
    without requiring MySQL timezone tables.
    """
    cutoff = timezone.now() - timedelta(days=days)
    dates = list(queryset.filter(**{f'{date_field}__gte': cutoff}).values_list(date_field, flat=True))

    counts = Counter()
    for d in dates:
        if d:
            counts[(d.year, d.month)] += 1

    now = timezone.now()
    num_months = max(3, min(12, (days // 30) + 1))

    ym_keys = []
    y, m = now.year, now.month
    for _ in range(num_months):
        ym_keys.append((y, m))
        m -= 1
        if m < 1:
            m = 12
            y -= 1
    ym_keys.reverse()

    months = []
    for y, m in ym_keys:
        val = counts.get((y, m), 0)
        label = calendar.month_abbr[m]
        months.append({
            'label': label,
            'value': val,
        })

    values = [item['value'] for item in months]
    max_value = max(values) if values else 1
    for item in months:
        item['percent'] = round((item['value'] / max_value) * 100, 1) if max_value else 0

    return months


def build_ai_insights():
    """
    Calculates platform-wide AI matching statistics, skill demands, and candidate distribution.
    """
    applications = Application.objects.filter(overall_match_score__gt=0)
    avg_match = applications.aggregate(avg=Avg('overall_match_score'))['avg'] or 0
    total_applications = applications.count()

    skill_counter = Counter()
    for profile in StudentProfile.objects.all():
        for skill in profile.get_skills_list():
            skill_counter[skill] += 1

    demand_counter = Counter()
    for job in Job.objects.filter(status=Job.STATUS_ACTIVE):
        for skill in job.get_all_skills():
            demand_counter[skill] += 1

    most_demanded = demand_counter.most_common(6)
    top_skills = skill_counter.most_common(6)

    high_match_candidates = applications.filter(overall_match_score__gte=80).count()
    shortlisted_candidates = applications.filter(
        status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW, Application.STATUS_ACCEPTED]
    ).count()

    skill_gap_students = 0
    for profile in StudentProfile.objects.all():
        skills = set(s.lower() for s in profile.get_skills_list())
        if not skills:
            continue
        if most_demanded and not any(skill.lower() in skills for skill in [item[0].lower() for item in most_demanded[:3]]):
            skill_gap_students += 1

    match_success_rate = 0
    if total_applications:
        match_success_rate = round((shortlisted_candidates / total_applications) * 100, 1)

    # Top categories — Job has no 'industry' field; derive from job_type
    job_type_counter = Counter(
        Job.objects.filter(status=Job.STATUS_ACTIVE)
        .exclude(job_type=Job.JOB_TYPE_INTERNSHIP)
        .values_list('job_type', flat=True)
    )
    top_job_category = job_type_counter.most_common(1)[0][0] if job_type_counter else 'Full-Time'
    # Make it human-readable
    type_labels = dict(Job._meta.get_field('job_type').choices) if hasattr(Job._meta.get_field('job_type'), 'choices') else {}
    top_job_category = type_labels.get(top_job_category, top_job_category) or top_job_category

    # Top internship category — use top skill demanded by internships
    internship_skill_counter = Counter()
    for job in Job.objects.filter(status=Job.STATUS_ACTIVE, job_type=Job.JOB_TYPE_INTERNSHIP):
        for skill in job.get_all_skills():
            internship_skill_counter[skill] += 1
    top_internship_category = (
        internship_skill_counter.most_common(1)[0][0] if internship_skill_counter else 'Software Engineering'
    )

    return {
        'average_match_score': round(float(avg_match), 1) if avg_match else 0,
        'most_demanded_skill': most_demanded[0][0] if most_demanded else 'Python',
        'fastest_growing_skill': most_demanded[1][0] if len(most_demanded) > 1 else 'Machine Learning',
        'top_job_category': top_job_category,
        'top_internship_category': top_internship_category,
        'most_recommended_category': 'Python / Backend' if demand_counter else 'Data & AI',
        'students_with_skill_gaps': skill_gap_students,
        'high_match_candidates': high_match_candidates,
        'ai_match_success_rate': match_success_rate,
        'top_skills': top_skills,
        'demand_skills': most_demanded,
        'total_evaluated_applications': total_applications,
    }


def build_recent_activity(limit=15):
    """
    Gathers real platform activity across students, recruiters, companies, jobs, and applications.
    """
    activities = []

    for student in User.objects.filter(role=User.ROLE_STUDENT).order_by('-date_joined')[:6]:
        activities.append({
            'icon': 'fa-user-graduate',
            'title': 'Student Registered',
            'entity': student.get_full_name() or student.username,
            'actor_name': student.get_full_name() or student.username,
            'action': 'Student account created',
            'target': 'Student profile',
            'timestamp': student.date_joined,
            'status': 'Active' if student.is_active else 'Inactive',
        })

    for recruiter in User.objects.filter(role=User.ROLE_RECRUITER).order_by('-date_joined')[:6]:
        activities.append({
            'icon': 'fa-building-user',
            'title': 'Recruiter Joined',
            'entity': recruiter.get_full_name() or recruiter.username,
            'actor_name': recruiter.get_full_name() or recruiter.username,
            'action': 'Recruiter account onboarded',
            'target': 'Recruiter profile',
            'timestamp': recruiter.date_joined,
            'status': 'Active' if recruiter.is_active else 'Inactive',
        })

    for company in Company.objects.order_by('-created_at')[:6]:
        activities.append({
            'icon': 'fa-building',
            'title': 'Company Registered',
            'entity': company.name,
            'actor_name': 'Platform System',
            'action': 'Company profile registered',
            'target': company.name,
            'timestamp': company.created_at,
            'status': 'Verified' if getattr(company, 'is_verified', True) else 'Pending',
        })

    for job in Job.objects.select_related('company').order_by('-created_at')[:6]:
        activities.append({
            'icon': 'fa-briefcase' if job.job_type != Job.JOB_TYPE_INTERNSHIP else 'fa-graduation-cap',
            'title': 'Job Posted' if job.job_type != Job.JOB_TYPE_INTERNSHIP else 'Internship Posted',
            'entity': f'{job.title} · {job.company.name if job.company else "Independent"}',
            'actor_name': job.company.name if job.company else 'Recruiter',
            'action': f'{job.get_job_type_display()} published',
            'target': job.title,
            'timestamp': job.created_at,
            'status': job.get_status_display(),
        })

    for application in Application.objects.select_related('student', 'job', 'job__company').order_by('-applied_at')[:6]:
        activities.append({
            'icon': 'fa-file-signature',
            'title': 'Application Submitted',
            'entity': f'{application.student.get_full_name() or application.student.username} → {application.job.title}',
            'actor_name': application.student.get_full_name() or application.student.username,
            'action': 'Application submitted with AI score',
            'target': application.job.title,
            'timestamp': application.applied_at,
            'status': application.get_status_display(),
        })

    activities.sort(key=lambda item: item['timestamp'], reverse=True)
    return activities[:limit]


# ==============================================================================
# ADMIN VIEWS
# ==============================================================================

@admin_required
def dashboard_view(request):
    student_count = User.objects.filter(role=User.ROLE_STUDENT).count()
    recruiter_count = User.objects.filter(role=User.ROLE_RECRUITER).count()
    company_count = Company.objects.count()
    active_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).count()
    active_internships = Job.objects.filter(status=Job.STATUS_ACTIVE, job_type=Job.JOB_TYPE_INTERNSHIP).count()
    total_applications = Application.objects.count()
    ai_matches = Application.objects.filter(overall_match_score__gt=0).count()
    shortlisted_candidates = Application.objects.filter(
        status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW, Application.STATUS_ACCEPTED]
    ).count()

    app_overview = {
        'applications': total_applications,
        'under_review': Application.objects.filter(status=Application.STATUS_REVIEWING).count(),
        'shortlisted': Application.objects.filter(
            status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW, Application.STATUS_ACCEPTED]
        ).count(),
        'rejected': Application.objects.filter(status=Application.STATUS_REJECTED).count(),
        'hired': Application.objects.filter(status=Application.STATUS_ACCEPTED).count(),
    }

    student_trend = build_monthly_trend(User.objects.filter(role=User.ROLE_STUDENT), 'date_joined', 180)
    recruiter_trend = build_monthly_trend(User.objects.filter(role=User.ROLE_RECRUITER), 'date_joined', 180)
    company_trend = build_monthly_trend(Company.objects.all(), 'created_at', 180)
    job_trend = build_monthly_trend(Job.objects.all(), 'created_at', 180)
    internship_trend = build_monthly_trend(Job.objects.filter(job_type=Job.JOB_TYPE_INTERNSHIP), 'created_at', 180)

    ai_insights = build_ai_insights()
    recent_activity = build_recent_activity(limit=10)
    recent_applications = Application.objects.select_related('student', 'job', 'job__company').order_by('-applied_at')[:8]

    context = {
        'student_count': student_count,
        'recruiter_count': recruiter_count,
        'company_count': company_count,
        'active_jobs': active_jobs,
        'active_internships': active_internships,
        'total_applications': total_applications,
        'ai_matches': ai_matches,
        'shortlisted_candidates': shortlisted_candidates,
        'app_overview': app_overview,
        'student_trend': student_trend,
        'recruiter_trend': recruiter_trend,
        'company_trend': company_trend,
        'job_trend': job_trend,
        'internship_trend': internship_trend,
        'ai_insights': ai_insights,
        'recent_activity': recent_activity,
        'recent_applications': recent_applications,
        'page_title': 'Admin Control Center',
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@admin_required
def students_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    students = StudentProfile.objects.select_related('user').order_by('-created_at')

    if query:
        students = students.filter(
            Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(skills__icontains=query)
            | Q(institution__icontains=query)
        )

    if status_filter == 'active':
        students = students.filter(user__is_active=True)
    elif status_filter == 'inactive':
        students = students.filter(user__is_active=False)

    paginator = Paginator(students, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'students': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'total_count': students.count(),
        'page_title': 'Student Management',
    }
    return render(request, 'admin_dashboard/students.html', context)


@admin_required
def student_detail_view(request, user_id):
    student = get_object_or_404(StudentProfile.objects.select_related('user'), user_id=user_id)
    educations = Education.objects.filter(student=student).order_by('-end_year')
    experiences = Experience.objects.filter(student=student).order_by('-start_date')
    certifications = Certification.objects.filter(student=student).order_by('-issue_date')
    applications = Application.objects.filter(student=student.user).select_related('job', 'job__company').order_by('-applied_at')

    context = {
        'student': student,
        'educations': educations,
        'experiences': experiences,
        'certifications': certifications,
        'applications': applications,
        'application_count': applications.count(),
        'page_title': f"Student: {student.user.get_full_name() or student.user.username}",
    }
    return render(request, 'admin_dashboard/student_detail.html', context)


@admin_required
def recruiters_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    company_filter = request.GET.get('company', '').strip()

    recruiters = RecruiterProfile.objects.select_related('user', 'company').order_by('-created_at')

    if query:
        recruiters = recruiters.filter(
            Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(company__name__icontains=query)
            | Q(designation__icontains=query)
        )

    if status_filter == 'active':
        recruiters = recruiters.filter(user__is_active=True)
    elif status_filter == 'inactive':
        recruiters = recruiters.filter(user__is_active=False)

    if company_filter:
        recruiters = recruiters.filter(company_id=company_filter)

    companies = Company.objects.all().order_by('name')
    paginator = Paginator(recruiters, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'recruiters': page_obj,
        'page_obj': page_obj,
        'companies': companies,
        'query': query,
        'status_filter': status_filter,
        'company_filter': company_filter,
        'total_count': recruiters.count(),
        'page_title': 'Recruiter Management',
    }
    return render(request, 'admin_dashboard/recruiters.html', context)


@admin_required
def recruiter_detail_view(request, user_id):
    recruiter = get_object_or_404(RecruiterProfile.objects.select_related('user', 'company'), user_id=user_id)
    jobs = Job.objects.filter(recruiter=recruiter.user).select_related('company').order_by('-created_at')
    applications = Application.objects.filter(job__recruiter=recruiter.user).select_related('student', 'job').order_by('-applied_at')

    context = {
        'recruiter': recruiter,
        'jobs': jobs,
        'applications': applications,
        'application_count': applications.count(),
        'page_title': f"Recruiter: {recruiter.user.get_full_name() or recruiter.user.username}",
    }
    return render(request, 'admin_dashboard/recruiter_detail.html', context)


@admin_required
def companies_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    verification_filter = request.GET.get('verified', '').strip()

    companies = Company.objects.all().prefetch_related('recruiters', 'jobs').order_by('-created_at')

    if query:
        companies = companies.filter(
            Q(name__icontains=query)
            | Q(industry__icontains=query)
            | Q(location__icontains=query)
        )

    if status_filter == 'active':
        companies = companies.filter(is_active=True)
    elif status_filter == 'inactive':
        companies = companies.filter(is_active=False)

    if verification_filter == 'yes':
        companies = companies.filter(is_verified=True)
    elif verification_filter == 'no':
        companies = companies.filter(is_verified=False)

    paginator = Paginator(companies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'companies': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'verification_filter': verification_filter,
        'total_count': companies.count(),
        'page_title': 'Company Management',
    }
    return render(request, 'admin_dashboard/companies.html', context)


@admin_required
def company_detail_view(request, company_id):
    company = get_object_or_404(Company.objects.prefetch_related('jobs', 'recruiters'), pk=company_id)
    jobs = company.jobs.select_related('recruiter').order_by('-created_at')
    recruiters = company.recruiters.select_related('user').all()
    application_count = Application.objects.filter(job__company=company).count()

    context = {
        'company': company,
        'jobs': jobs,
        'recruiters': recruiters,
        'recruiter_count': recruiters.count(),
        'application_count': application_count,
        'page_title': f"Company: {company.name}",
    }
    return render(request, 'admin_dashboard/company_detail.html', context)


@admin_required
def jobs_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    job_type = request.GET.get('type', '').strip()
    work_mode = request.GET.get('mode', '').strip()
    company_id = request.GET.get('company_id', '').strip()

    jobs = Job.objects.select_related('company', 'recruiter').order_by('-created_at')

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__name__icontains=query)
            | Q(required_skills__icontains=query)
            | Q(location__icontains=query)
        )

    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)
    if company_id:
        jobs = jobs.filter(company_id=company_id)

    companies = Company.objects.all().order_by('name')
    paginator = Paginator(jobs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'jobs': page_obj,
        'page_obj': page_obj,
        'companies': companies,
        'query': query,
        'status_filter': status_filter,
        'type_filter': job_type,
        'mode_filter': work_mode,
        'company_id': company_id,
        'status_choices': Job.STATUS_CHOICES,
        'type_choices': Job.JOB_TYPE_CHOICES,
        'mode_choices': Job.WORK_MODE_CHOICES,
        'total_count': jobs.count(),
        'page_title': 'Job Management',
    }
    return render(request, 'admin_dashboard/jobs.html', context)


@admin_required
def internships_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    work_mode = request.GET.get('mode', '').strip()

    internships = Job.objects.filter(job_type=Job.JOB_TYPE_INTERNSHIP).select_related('company', 'recruiter').order_by('-created_at')

    if query:
        internships = internships.filter(
            Q(title__icontains=query)
            | Q(company__name__icontains=query)
            | Q(required_skills__icontains=query)
            | Q(location__icontains=query)
        )

    if status_filter:
        internships = internships.filter(status=status_filter)
    if work_mode:
        internships = internships.filter(work_mode=work_mode)

    paginator = Paginator(internships, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'internships': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'mode_filter': work_mode,
        'status_choices': Job.STATUS_CHOICES,
        'mode_choices': Job.WORK_MODE_CHOICES,
        'total_count': internships.count(),
        'page_title': 'Internship Management',
    }
    return render(request, 'admin_dashboard/internships.html', context)


@admin_required
def applications_view(request):
    query = request.GET.get('q', '').strip()
    company_id = request.GET.get('company_id', '').strip()
    status = request.GET.get('status', '').strip()
    match_score = request.GET.get('match_score', '').strip()

    applications = Application.objects.select_related('student', 'job', 'job__company').order_by('-applied_at')

    if query:
        applications = applications.filter(
            Q(student__first_name__icontains=query)
            | Q(student__last_name__icontains=query)
            | Q(student__username__icontains=query)
            | Q(job__title__icontains=query)
            | Q(job__company__name__icontains=query)
        )

    if company_id:
        applications = applications.filter(job__company_id=company_id)
    if status:
        applications = applications.filter(status=status)

    if match_score == '90':
        applications = applications.filter(overall_match_score__gte=90)
    elif match_score == '80':
        applications = applications.filter(overall_match_score__gte=80, overall_match_score__lt=90)
    elif match_score == '70':
        applications = applications.filter(overall_match_score__gte=70, overall_match_score__lt=80)
    elif match_score == 'below70':
        applications = applications.filter(overall_match_score__lt=70)

    companies = Company.objects.all().order_by('name')
    paginator = Paginator(applications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'applications': page_obj,
        'page_obj': page_obj,
        'companies': companies,
        'query': query,
        'company_id': company_id,
        'status': status,
        'match_score': match_score,
        'status_choices': Application.STATUS_CHOICES,
        'total_count': applications.count(),
        'page_title': 'Application Management',
    }
    return render(request, 'admin_dashboard/applications.html', context)


@admin_required
def ai_insights_view(request):
    insights = build_ai_insights()
    high_match_apps = Application.objects.filter(overall_match_score__gte=80).select_related('student', 'job', 'job__company').order_by('-overall_match_score')[:8]

    context = {
        'insights': insights,
        'high_match_apps': high_match_apps,
        'page_title': 'AI Recruitment Insights',
    }
    return render(request, 'admin_dashboard/ai_insights.html', context)


@admin_required
def analytics_view(request):
    range_days = int(request.GET.get('range', '30'))
    if range_days not in (7, 30, 90, 180, 365):
        range_days = 30

    student_trend = build_monthly_trend(User.objects.filter(role=User.ROLE_STUDENT), 'date_joined', range_days)
    recruiter_trend = build_monthly_trend(User.objects.filter(role=User.ROLE_RECRUITER), 'date_joined', range_days)
    company_trend = build_monthly_trend(Company.objects.all(), 'created_at', range_days)
    job_trend = build_monthly_trend(Job.objects.all(), 'created_at', range_days)
    internship_trend = build_monthly_trend(Job.objects.filter(job_type=Job.JOB_TYPE_INTERNSHIP), 'created_at', range_days)
    application_trend = build_monthly_trend(Application.objects.all(), 'applied_at', range_days)

    app_funnel = {
        'applied': Application.objects.count(),
        'reviewing': Application.objects.filter(status=Application.STATUS_REVIEWING).count(),
        'shortlisted': Application.objects.filter(
            status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW]
        ).count(),
        'accepted': Application.objects.filter(status=Application.STATUS_ACCEPTED).count(),
        'rejected': Application.objects.filter(status=Application.STATUS_REJECTED).count(),
    }

    ai_data = build_ai_insights()

    context = {
        'range_days': range_days,
        'student_trend': student_trend,
        'recruiter_trend': recruiter_trend,
        'company_trend': company_trend,
        'job_trend': job_trend,
        'internship_trend': internship_trend,
        'application_trend': application_trend,
        'app_funnel': app_funnel,
        'ai_data': ai_data,
        'page_title': 'Platform Analytics',
    }
    return render(request, 'admin_dashboard/analytics.html', context)


@admin_required
def reports_view(request):
    export = request.GET.get('export')

    # CSV EXPORTS
    if export == 'students':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['User ID', 'Username', 'Full Name', 'Email', 'Institution', 'Degree', 'Status', 'Joined Date'])
        for s in StudentProfile.objects.select_related('user').all():
            writer.writerow([
                s.user.id, s.user.username, s.user.get_full_name(), s.user.email,
                s.institution, s.degree, 'Active' if s.user.is_active else 'Inactive',
                s.user.date_joined.strftime('%Y-%m-%d')
            ])
        return response

    elif export == 'recruiters':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recruiters_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['User ID', 'Username', 'Full Name', 'Email', 'Company', 'Designation', 'Status', 'Joined Date'])
        for r in RecruiterProfile.objects.select_related('user', 'company').all():
            writer.writerow([
                r.user.id, r.user.username, r.user.get_full_name(), r.user.email,
                r.company.name if r.company else 'Independent', r.designation,
                'Active' if r.user.is_active else 'Inactive', r.user.date_joined.strftime('%Y-%m-%d')
            ])
        return response

    elif export == 'companies':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="companies_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Company ID', 'Name', 'Industry', 'Location', 'Website', 'Verified', 'Active', 'Created Date'])
        for c in Company.objects.all():
            writer.writerow([
                c.id, c.name, c.industry, c.location, c.website,
                'Verified' if c.is_verified else 'Pending',
                'Active' if c.is_active else 'Inactive',
                c.created_at.strftime('%Y-%m-%d')
            ])
        return response

    elif export == 'jobs':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="jobs_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Job ID', 'Title', 'Company', 'Type', 'Work Mode', 'Status', 'Applications', 'Posted Date'])
        for j in Job.objects.select_related('company').all():
            writer.writerow([
                j.id, j.title, j.company.name if j.company else 'N/A',
                j.get_job_type_display(), j.get_work_mode_display(),
                j.get_status_display(), j.applications.count(),
                j.created_at.strftime('%Y-%m-%d')
            ])
        return response

    elif export == 'applications':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['App ID', 'Candidate', 'Email', 'Job Title', 'Company', 'Match Score', 'Status', 'Applied Date'])
        for a in Application.objects.select_related('student', 'job', 'job__company').all():
            writer.writerow([
                a.id, a.student.get_full_name() or a.student.username, a.student.email,
                a.job.title, a.job.company.name if a.job.company else 'N/A',
                f"{a.overall_match_score}%", a.get_status_display(),
                a.applied_at.strftime('%Y-%m-%d %H:%M')
            ])
        return response

    student_count = User.objects.filter(role=User.ROLE_STUDENT).count()
    recruit_count = User.objects.filter(role=User.ROLE_RECRUITER).count()
    company_count = Company.objects.count()
    job_count = Job.objects.count()
    active_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).count()
    internship_count = Job.objects.filter(job_type=Job.JOB_TYPE_INTERNSHIP).count()
    app_count = Application.objects.count()
    matched_applications = Application.objects.filter(overall_match_score__gt=0).count()
    shortlisted_count = Application.objects.filter(
        status__in=[Application.STATUS_SHORTLISTED, Application.STATUS_INTERVIEW, Application.STATUS_ACCEPTED]
    ).count()
    hired_count = Application.objects.filter(status=Application.STATUS_ACCEPTED).count()
    avg_match_score = Application.objects.filter(overall_match_score__gt=0).aggregate(avg=Avg('overall_match_score'))['avg'] or 0
    pending_reviews = Application.objects.filter(status=Application.STATUS_REVIEWING).count()

    report = {
        'students': student_count,
        'recruiters': recruit_count,
        'companies': company_count,
        'jobs': job_count,
        'internships': internship_count,
        'applications': app_count,
        'ai': matched_applications,
        'skills': active_jobs,
        'applied': app_count,
        'shortlisted': shortlisted_count,
        'hired': hired_count,
        'conversion_rate': round((shortlisted_count / app_count) * 100, 1) if app_count else 0,
        'avg_applications_per_job': round(app_count / job_count, 1) if job_count else 0,
        'avg_match_score': round(float(avg_match_score), 1) if avg_match_score else 0,
        'pending_reviews': pending_reviews,
    }
    context = {'report': report, 'page_title': 'Executive Reports'}
    return render(request, 'admin_dashboard/reports.html', context)


@admin_required
def activity_logs_view(request):
    filter_type = request.GET.get('type', 'all')
    all_activities = build_recent_activity(limit=40)

    if filter_type == 'students':
        activities = [a for a in all_activities if 'Student' in a['title']]
    elif filter_type == 'recruiters':
        activities = [a for a in all_activities if 'Recruiter' in a['title']]
    elif filter_type == 'companies':
        activities = [a for a in all_activities if 'Company' in a['title']]
    elif filter_type == 'jobs':
        activities = [a for a in all_activities if 'Job' in a['title'] or 'Internship' in a['title']]
    elif filter_type == 'applications':
        activities = [a for a in all_activities if 'Application' in a['title']]
    else:
        activities = all_activities

    context = {
        'activities': activities,
        'filter_type': filter_type,
        'page_title': 'Platform Activity Logs',
    }
    return render(request, 'admin_dashboard/activity_logs.html', context)


@admin_required
def settings_view(request):
    default_settings = {
        'platform_name': 'CareerAI Enterprise Platform',
        'default_company_status': 'verified',
        'auto_match_threshold': 80,
        'job_expiry_days': 60,
        'email_notifications': True,
        'updated_at': timezone.now(),
    }
    saved_settings = request.session.get('admin_dashboard_settings', default_settings)

    if request.method == 'POST':
        saved_settings = {
            'platform_name': request.POST.get('platform_name', saved_settings.get('platform_name', default_settings['platform_name'])),
            'default_company_status': request.POST.get('default_company_status', saved_settings.get('default_company_status', default_settings['default_company_status'])),
            'auto_match_threshold': int(request.POST.get('auto_match_threshold', saved_settings.get('auto_match_threshold', default_settings['auto_match_threshold']))),
            'job_expiry_days': int(request.POST.get('job_expiry_days', saved_settings.get('job_expiry_days', default_settings['job_expiry_days']))),
            'email_notifications': request.POST.get('email_notifications') == 'on',
            'updated_at': timezone.now(),
        }
        request.session['admin_dashboard_settings'] = saved_settings
        messages.success(request, "Platform settings saved successfully.")

    context = {'settings': saved_settings, 'page_title': 'Platform Settings'}
    return render(request, 'admin_dashboard/settings.html', context)


# ==============================================================================
# ADMIN ACTIONS (TOGGLES & MANAGEMENT)
# ==============================================================================

@require_POST
@admin_required
def toggle_user_status_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser or user.role == User.ROLE_ADMIN:
        messages.error(request, "Cannot deactivate system administrators.")
        return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status_str = "activated" if user.is_active else "deactivated"
    messages.success(request, f"Account for '{user.username}' has been {status_str}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@require_POST
@admin_required
def toggle_company_verification_view(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    company.is_verified = not company.is_verified
    company.save(update_fields=['is_verified'])
    status_str = "verified" if company.is_verified else "marked as unverified"
    messages.success(request, f"Company '{company.name}' is now {status_str}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_companies'))


@require_POST
@admin_required
def toggle_company_status_view(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    company.is_active = not company.is_active
    company.save(update_fields=['is_active'])
    status_str = "activated" if company.is_active else "deactivated"
    messages.success(request, f"Company '{company.name}' has been {status_str}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_companies'))


@require_POST
@admin_required
def toggle_job_status_view(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    job.status = Job.STATUS_CLOSED if job.status == Job.STATUS_ACTIVE else Job.STATUS_ACTIVE
    job.save(update_fields=['status'])
    messages.success(request, f"Opportunity '{job.title}' status changed to {job.get_status_display()}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_jobs'))
