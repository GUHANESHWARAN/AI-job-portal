from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    headline = models.CharField(max_length=200, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    degree = models.CharField(max_length=150, blank=True, default='')
    institution = models.CharField(max_length=200, blank=True, default='')
    graduation_year = models.IntegerField(null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=150, blank=True, default='')

    # Links
    github_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    portfolio_url = models.URLField(blank=True, default='')

    # Skills
    skills = models.TextField(blank=True, default='', help_text="Comma-separated skills list")

    # Resume & AI Insights
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True)
    parsed_resume_text = models.TextField(blank=True, default='')
    extracted_skills = models.JSONField(default=list, blank=True)
    resume_sections = models.JSONField(default=dict, blank=True)
    ats_score = models.IntegerField(default=0)
    ats_feedback = models.JSONField(default=list, blank=True)

    # Preferences
    preferred_job_titles = models.CharField(max_length=255, blank=True, default='')
    preferred_locations = models.CharField(max_length=255, blank=True, default='')
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_skills_list(self):
        """Combines manually entered skills and AI extracted skills deduplicated."""
        manual = [s.strip() for s in self.skills.split(',') if s.strip()] if self.skills else []
        extracted = self.extracted_skills if isinstance(self.extracted_skills, list) else []
        combined = []
        seen = set()
        for s in manual + extracted:
            s_clean = s.strip()
            if s_clean and s_clean.lower() not in seen:
                seen.add(s_clean.lower())
                combined.append(s_clean)
        return combined

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.degree or 'Student'})"


class Education(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=150)
    field_of_study = models.CharField(max_length=150, blank=True, default='')
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True, default='')
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-end_year', '-start_year']

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class Experience(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150, blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} at {self.company}"


class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    technologies = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    github_url = models.URLField(blank=True, default='')
    live_url = models.URLField(blank=True, default='')

    def __str__(self):
        return self.title


class Certification(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    credential_url = models.URLField(blank=True, default='')

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"
