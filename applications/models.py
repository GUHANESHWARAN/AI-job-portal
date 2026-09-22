from django.conf import settings
from django.db import models
from jobs.models import Job


class Application(models.Model):
    STATUS_APPLIED = 'applied'
    STATUS_REVIEWING = 'reviewing'
    STATUS_SHORTLISTED = 'shortlisted'
    STATUS_INTERVIEW = 'interview'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_APPLIED, 'Applied'),
        (STATUS_REVIEWING, 'Under Review'),
        (STATUS_SHORTLISTED, 'Shortlisted'),
        (STATUS_INTERVIEW, 'Interview Scheduled'),
        (STATUS_ACCEPTED, 'Offer Extended'),
        (STATUS_REJECTED, 'Not Selected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    cover_letter = models.TextField(blank=True, default='')
    resume_file = models.FileField(upload_to='application_resumes/', blank=True, null=True)

    # AI Match Score Snapshots at application time
    overall_match_score = models.FloatField(default=0.0)
    skill_match_score = models.FloatField(default=0.0)
    semantic_match_score = models.FloatField(default=0.0)
    experience_match_score = models.FloatField(default=0.0)
    match_explanation = models.JSONField(default=dict, blank=True)

    # Recruitment Pipeline Status
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_APPLIED)
    recruiter_notes = models.TextField(blank=True, default='')

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-overall_match_score', '-applied_at']
        constraints = [
            models.UniqueConstraint(fields=['job', 'student'], name='unique_job_application')
        ]

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} -> {self.job.title} ({self.overall_match_score:.1f}% match)"
