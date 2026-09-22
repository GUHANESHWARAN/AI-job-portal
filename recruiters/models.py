from django.conf import settings
from django.db import models
from companies.models import Company


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruiter_profile'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruiters'
    )
    designation = models.CharField(max_length=150, blank=True, default='Talent Acquisition Lead')
    department = models.CharField(max_length=120, blank=True, default='Human Resources')
    linkedin_url = models.URLField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        comp = self.company.name if self.company else "Independent Recruiter"
        return f"{self.user.get_full_name() or self.user.username} ({self.designation} at {comp})"
