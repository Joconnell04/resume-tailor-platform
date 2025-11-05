"""
Tailoring app serializers

Serializers for TailoringSession model.
"""
from rest_framework import serializers
from .models import TailoringSession


class TailoringSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for TailoringSession.
    
    Exposes all session data including AI-generated outputs.
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company', read_only=True)
    
    class Meta:
        model = TailoringSession
        fields = [
            'id',
            'user',
            'username',
            'job',
            'job_title',
            'job_company',
            'input_experience_snapshot',
            'generated_title',
            'generated_bullets',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'input_experience_snapshot',
            'generated_title',
            'generated_bullets',
            'status',
            'created_at',
            'updated_at',
        ]


class TailoringSessionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new tailoring session.
    
    Only requires job_id; everything else is derived.
    """
    
    job_id = serializers.IntegerField()
