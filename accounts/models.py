"""
Accounts app models

Custom User model extending AbstractUser with role-based access and token quota.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role and token quota tracking.
    
    Extends Django's AbstractUser to add:
    - role: Distinguish between admins and job seekers
    - token_quota: Maximum tokens allowed for AI operations
    - tokens_used: Track consumed tokens
    """
    
    ADMIN = 'ADMIN'
    JOB_SEEKER = 'JOB_SEEKER'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (JOB_SEEKER, 'Job Seeker'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=JOB_SEEKER,
    )
    token_quota = models.IntegerField(default=1000)
    tokens_used = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
