from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_RECRUITER = 'recruiter'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = (
        (ROLE_STUDENT, 'Student / Job Seeker'),
        (ROLE_RECRUITER, 'Recruiter / Employer'),
        (ROLE_ADMIN, 'System Administrator'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=20, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def is_recruiter(self):
        return self.role == self.ROLE_RECRUITER

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.username}) [{self.get_role_display()}]" if full_name else f"{self.username} [{self.get_role_display()}]"
