from django.conf import settings
from django.db import models
from jobs.models import Job


class Application(models.Model):
    # Original statuses (backward compatible with existing DB data)
    STATUS_APPLIED = 'applied'
    STATUS_REVIEWING = 'reviewing'
    STATUS_SHORTLISTED = 'shortlisted'
    STATUS_INTERVIEW = 'interview'
    STATUS_SELECTED = 'selected'      # New: post-interview selection
    STATUS_OFFERED = 'offered'        # New: formal offer made (triggers offer letter PDF)
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_APPLIED, 'Applied'),
        (STATUS_REVIEWING, 'Under Review'),
        (STATUS_SHORTLISTED, 'Shortlisted'),
        (STATUS_INTERVIEW, 'Interview Scheduled'),
        (STATUS_SELECTED, 'Selected'),
        (STATUS_OFFERED, 'Offer Extended'),
        (STATUS_ACCEPTED, 'Accepted'),
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

    # Offer Letter (internship only) — generated when status becomes STATUS_OFFERED
    offer_letter_file = models.FileField(
        upload_to='offer_letters/', blank=True, null=True,
        help_text='PDF offer letter generated for internship offers'
    )
    offer_letter_sent_at = models.DateTimeField(blank=True, null=True)

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-overall_match_score', '-applied_at']
        constraints = [
            models.UniqueConstraint(fields=['job', 'student'], name='unique_job_application')
        ]

    @property
    def is_internship(self):
        from jobs.models import Job
        return self.job.job_type == Job.JOB_TYPE_INTERNSHIP

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} -> {self.job.title} ({self.overall_match_score:.1f}% match)"
