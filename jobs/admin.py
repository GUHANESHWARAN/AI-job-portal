from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'work_mode', 'experience_level', 'status', 'created_at')
    list_filter = ('job_type', 'work_mode', 'experience_level', 'status', 'company')
    search_fields = ('title', 'description', 'company__name', 'location')
