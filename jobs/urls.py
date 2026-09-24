from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('internships/', views.internship_list_view, name='internship_list'),
    path('<int:pk>/', views.job_detail_view, name='job_detail'),
    path('api/extract-skills/', views.extract_skills_preview_api, name='api_extract_skills'),
]

