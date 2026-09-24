from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/', views.company_detail_view, name='company_detail'),
]

