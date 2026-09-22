"""
URL configuration for AI_Job_Portal project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from accounts.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('student/', include('students.urls')),
    path('recruiter/', include('recruiters.urls')),
    path('jobs/', include('jobs.urls')),
    path('companies/', include('companies.urls')),
    path('applications/', include('applications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
