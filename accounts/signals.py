from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from students.models import StudentProfile
from recruiters.models import RecruiterProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.ROLE_STUDENT:
            StudentProfile.objects.get_or_create(user=instance)
        elif instance.role == User.ROLE_RECRUITER:
            RecruiterProfile.objects.get_or_create(user=instance)
