"""
Jobs app models

JobPosting model for storing job opportunities from various sources.
"""
from django.conf import settings
from django.db import models


class JobPosting(models.Model):
    """
    Store job postings from pasted descriptions or URLs.
    
    Supports two input methods:
    1. Direct paste of job description into raw_description
    2. URL for later scraping (source_url)
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='job_postings',
    )
    title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)
    raw_description = models.TextField(blank=True)
    location_text = models.CharField(max_length=255, blank=True)
    parsed_requirements = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        title = self.title or "Untitled Job"
        company = self.company or "Unknown Company"
        return f"{title} at {company}"

    def get_tailoring_stats(self):
        """Returns aggregated stats about tailoring sessions"""
        from django.db.models import Sum, Q
        sessions = self.tailoring_sessions.all()
        total = sessions.count()

        if total == 0:
            return {
                'total': 0,
                'completed': 0,
                'processing': 0,
                'failed': 0,
                'pending': 0,
                'total_tokens': 0,
                'latest_session': None,
                'success_rate': 0,
                'recent_sessions': []
            }

        completed = sessions.filter(status='COMPLETED').count()
        processing = sessions.filter(status='PROCESSING').count()
        failed = sessions.filter(status='FAILED').count()
        pending = sessions.filter(status='PENDING').count()

        # Calculate total tokens
        token_sum = sessions.aggregate(
            total=Sum('token_usage__total_tokens')
        )['total'] or 0

        # Calculate success rate
        success_rate = round((completed / total * 100)) if total > 0 else 0

        # Get recent sessions (last 3)
        recent = sessions[:3]

        return {
            'total': total,
            'completed': completed,
            'processing': processing,
            'failed': failed,
            'pending': pending,
            'total_tokens': token_sum,
            'latest_session': sessions.first(),
            'success_rate': success_rate,
            'recent_sessions': recent
        }

    class Meta:
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        ordering = ['-created_at']
