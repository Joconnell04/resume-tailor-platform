"""
Tailoring app models

TailoringSession model for storing AI-generated resume tailoring history.
"""
from django.conf import settings
from django.db import models


class TailoringSession(models.Model):
    """
    Store history of AI tailoring sessions.
    
    Each session represents one attempt to tailor a user's experience
    to a specific job posting using AI.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tailoring_sessions',
    )
    job = models.ForeignKey(
        'jobs.JobPosting',
        on_delete=models.CASCADE,
        related_name='tailoring_sessions',
    )
    
    # Snapshot of experience at time of tailoring
    input_experience_snapshot = models.JSONField(default=dict)
    
    # AI-generated outputs
    generated_title = models.CharField(max_length=255, blank=True)
    generated_bullets = models.JSONField(default=list)  # List of bullet strings
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Tailoring session for {self.user.username} - {self.job.title}"
    
    class Meta:
        verbose_name = 'Tailoring Session'
        verbose_name_plural = 'Tailoring Sessions'
        ordering = ['-created_at']
