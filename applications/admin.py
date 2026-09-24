from django.contrib import admin
from .models import Application

# Register your models here.

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'overall_match_score', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('student__username', 'student__email', 'job__title', 'job__company__name')
