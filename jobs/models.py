from django.conf import settings
from django.db import models
from companies.models import Company


class Job(models.Model):
    JOB_TYPE_FULL_TIME = 'full_time'
    JOB_TYPE_PART_TIME = 'part_time'
    JOB_TYPE_INTERNSHIP = 'internship'
    JOB_TYPE_CONTRACT = 'contract'

    JOB_TYPE_CHOICES = (
        (JOB_TYPE_FULL_TIME, 'Full-time Job'),
        (JOB_TYPE_PART_TIME, 'Part-time Job'),
        (JOB_TYPE_INTERNSHIP, 'Internship'),
        (JOB_TYPE_CONTRACT, 'Contract / Freelance'),
    )

    WORK_MODE_REMOTE = 'remote'
    WORK_MODE_HYBRID = 'hybrid'
    WORK_MODE_ONSITE = 'on_site'

    WORK_MODE_CHOICES = (
        (WORK_MODE_REMOTE, 'Remote / Work From Home'),
        (WORK_MODE_HYBRID, 'Hybrid'),
        (WORK_MODE_ONSITE, 'On-Site / Office'),
    )

    EXP_INTERN = 'intern'
    EXP_ENTRY = 'entry'
    EXP_MID = 'mid'
    EXP_SENIOR = 'senior'
    EXP_LEAD = 'lead'

    EXPERIENCE_CHOICES = (
        (EXP_INTERN, 'Internship / Student (0 years)'),
        (EXP_ENTRY, 'Entry Level / Fresher (0-2 years)'),
        (EXP_MID, 'Mid Level (2-5 years)'),
        (EXP_SENIOR, 'Senior Level (5-8 years)'),
        (EXP_LEAD, 'Lead / Principal (8+ years)'),
    )

    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_CLOSED, 'Closed'),
    )

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    title = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default=JOB_TYPE_FULL_TIME)
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default=WORK_MODE_REMOTE)
    location = models.CharField(max_length=150, blank=True, default='')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default=EXP_ENTRY)
    min_experience_years = models.IntegerField(default=0)

    # Compensation
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_salary_negotiable = models.BooleanField(default=True)

    # Job Content
    description = models.TextField()
    responsibilities = models.TextField(blank=True, default='')
    requirements = models.TextField(blank=True, default='')

    # AI Intelligence Fields
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    ai_summary = models.TextField(blank=True, default='')

    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_internship(self):
        return self.job_type == self.JOB_TYPE_INTERNSHIP

    def get_all_skills(self):
        skills = []
        if isinstance(self.required_skills, list):
            skills.extend(self.required_skills)
        if isinstance(self.preferred_skills, list):
            skills.extend(self.preferred_skills)
        return list(dict.fromkeys(skills))

    def __str__(self):
        return f"{self.title} at {self.company.name} ({self.get_job_type_display()})"
