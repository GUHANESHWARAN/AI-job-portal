from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    SIZE_CHOICES = (
        ('1-10', '1-10 employees (Startup)'),
        ('11-50', '11-50 employees (Small)'),
        ('51-200', '51-200 employees (Medium)'),
        ('201-1000', '201-1000 employees (Mid-Enterprise)'),
        ('1000+', '1000+ employees (Large Enterprise)'),
    )

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    website = models.URLField(blank=True, default='')
    industry = models.CharField(max_length=120, blank=True, default='Technology')
    company_size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='51-200')
    location = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='')
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
