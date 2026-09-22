from django.urls import path
from . import views

urlpatterns = [
    path('apply/<int:job_id>/', views.apply_job_view, name='apply_job'),
    path('withdraw/<int:application_id>/', views.withdraw_application_view, name='withdraw_application'),
]
