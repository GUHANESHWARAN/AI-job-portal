from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.recruiter_dashboard_view, name='recruiter_dashboard'),
    path('profile/', views.recruiter_profile_view, name='recruiter_profile'),
    path('jobs/create/', views.recruiter_create_job_view, name='recruiter_create_job'),
    path('jobs/<int:pk>/edit/', views.recruiter_edit_job_view, name='recruiter_edit_job'),
    path('jobs/manage/', views.recruiter_manage_jobs_view, name='recruiter_manage_jobs'),
    path('applications/', views.recruiter_applications_view, name='recruiter_applications'),
    path('candidates/', views.recruiter_candidates_view, name='recruiter_candidates'),
    path('candidates/<int:user_id>/', views.recruiter_candidate_profile_view, name='recruiter_candidate_profile'),
    path('api/applications/<int:application_id>/status/', views.update_application_status_api, name='api_update_app_status'),
]
