"""
Jobs app serializers

Serializers for JobPosting model.
"""
from rest_framework import serializers
from .models import JobPosting


class JobPostingSerializer(serializers.ModelSerializer):
    """
    Serializer for JobPosting.
    
    Accepts either raw_description or source_url (or both).
    User is automatically set from request context.
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = JobPosting
        fields = [
            'id',
            'user',
            'username',
            'title',
            'company',
            'source_url',
            'raw_description',
            'location_text',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at']
