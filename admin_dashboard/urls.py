from django.urls import path
from . import views

urlpatterns = [
    # Core Dashboard & Views
    path('', views.dashboard_view, name='admin_dashboard'),
    path('students/', views.students_view, name='admin_students'),
    path('students/<int:user_id>/', views.student_detail_view, name='admin_student_detail'),
    path('recruiters/', views.recruiters_view, name='admin_recruiters'),
    path('recruiters/<int:user_id>/', views.recruiter_detail_view, name='admin_recruiter_detail'),
    path('companies/', views.companies_view, name='admin_companies'),
    path('companies/<int:company_id>/', views.company_detail_view, name='admin_company_detail'),
    path('jobs/', views.jobs_view, name='admin_jobs'),
    path('internships/', views.internships_view, name='admin_internships'),
    path('applications/', views.applications_view, name='admin_applications'),
    path('ai-insights/', views.ai_insights_view, name='admin_ai_insights'),
    path('analytics/', views.analytics_view, name='admin_analytics'),
    path('reports/', views.reports_view, name='admin_reports'),
    path('activity-logs/', views.activity_logs_view, name='admin_activity_logs'),
    path('settings/', views.settings_view, name='admin_settings'),

    # Administrative Actions (POST)
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status_view, name='admin_toggle_user_status'),
    path('companies/<int:company_id>/toggle-verification/', views.toggle_company_verification_view, name='admin_toggle_company_verification'),
    path('companies/<int:company_id>/toggle-status/', views.toggle_company_status_view, name='admin_toggle_company_status'),
    path('jobs/<int:job_id>/toggle-status/', views.toggle_job_status_view, name='admin_toggle_job_status'),
]
