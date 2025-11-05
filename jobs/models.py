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
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        title = self.title or "Untitled Job"
        company = self.company or "Unknown Company"
        return f"{title} at {company}"
    
    class Meta:
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        ordering = ['-created_at']
