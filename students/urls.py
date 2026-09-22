from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('profile/', views.student_profile_view, name='student_profile'),
    path('resume/', views.student_resume_view, name='student_resume'),
    path('recommendations/', views.student_recommendations_view, name='student_recommendations'),
    path('skill-gap/', views.student_skill_gap_view, name='student_skill_gap'),
    path('applications/', views.student_applications_view, name='student_applications'),
]
