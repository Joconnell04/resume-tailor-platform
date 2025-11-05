from django.contrib import admin
from .models import TailoringSession


@admin.register(TailoringSession)
class TailoringSessionAdmin(admin.ModelAdmin):
    """Admin interface for TailoringSession."""
    
    list_display = [
        'id',
        'user',
        'job',
        'generated_title',
        'status',
        'created_at',
        'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = [
        'user__username',
        'job__title',
        'job__company',
        'generated_title'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'job', 'status')
        }),
        ('Input Data', {
            'fields': ('input_experience_snapshot',),
            'classes': ('collapse',)
        }),
        ('Generated Output', {
            'fields': ('generated_title', 'generated_bullets')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
