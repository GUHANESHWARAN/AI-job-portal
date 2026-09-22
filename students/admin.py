from django.contrib import admin
from .models import StudentProfile, Education, Experience, Project, Certification


class EducationInline(admin.TabularInline):
    model = Education
    extra = 1


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 1


class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'degree', 'institution', 'graduation_year', 'cgpa', 'ats_score', 'created_at')
    search_fields = ('user__username', 'user__email', 'degree', 'institution', 'skills')
    list_filter = ('graduation_year', 'degree')
    inlines = [EducationInline, ExperienceInline, ProjectInline, CertificationInline]
