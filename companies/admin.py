from django.contrib import admin
from .models import Company

# Register your models here.

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'company_size', 'location', 'website', 'created_at')
    search_fields = ('name', 'industry', 'location')
    prepopulated_fields = {'slug': ('name',)}
