from django.contrib import admin
from .models import JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    """Admin interface for JobPosting."""
    
    list_display = ['title', 'company', 'user', 'location_text', 'created_at']
    list_filter = ['created_at', 'company']
    search_fields = ['title', 'company', 'user__username', 'location_text', 'raw_description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'title', 'company', 'location_text')
        }),
        ('Source', {
            'fields': ('source_url', 'raw_description')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
