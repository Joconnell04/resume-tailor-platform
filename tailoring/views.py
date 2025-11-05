"""
Tailoring app views

ViewSet for TailoringSession with AI workflow integration.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404

from accounts.utils import check_and_increment_tokens
from experience.models import ExperienceGraph
from jobs.models import JobPosting

from .models import TailoringSession
from .serializers import TailoringSessionSerializer, TailoringSessionCreateSerializer
from .services import AgentKitTailoringService


class TailoringSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TailoringSession.
    
    - POST: Create new tailoring session with job_id
    - GET: List current user's sessions
    - GET {id}: Retrieve specific session
    - POST {id}/restart/: Clone and re-run a session
    """
    
    serializer_class = TailoringSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter to show only current user's tailoring sessions.
        Admins can see all sessions.
        """
        if self.request.user.role == 'ADMIN':
            return TailoringSession.objects.all()
        return TailoringSession.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new tailoring session.
        
        Flow:
        1. Validate job_id
        2. Check token quota
        3. Load user's experience graph
        4. Call AgentKit service
        5. Save results
        6. Increment tokens
        """
        # Validate input
        create_serializer = TailoringSessionCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        
        job_id = create_serializer.validated_data['job_id']
        
        # Get job posting
        job = get_object_or_404(JobPosting, id=job_id, user=request.user)
        
        # Check token quota (estimate 1 token per request)
        # TODO: Adjust cost based on actual token usage from OpenAI
        try:
            check_and_increment_tokens(request.user, cost=1)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Load user's experience graph
        try:
            experience_graph = ExperienceGraph.objects.get(user=request.user)
            experience_data = experience_graph.graph_json
        except ExperienceGraph.DoesNotExist:
            return Response(
                {'error': 'Experience graph not found. Please create your experience profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create session
        session = TailoringSession.objects.create(
            user=request.user,
            job=job,
            input_experience_snapshot=experience_data,
            status='PROCESSING',
        )
        
        # Call AgentKit service
        try:
            service = AgentKitTailoringService()
            
            # Use raw_description if available, otherwise indicate URL scraping needed
            job_description = job.raw_description
            if not job_description and job.source_url:
                # TODO: Implement URL scraping in service
                job_description = f"[URL to scrape: {job.source_url}]"
            
            result = service.run_workflow(
                job_description=job_description,
                experience_graph=experience_data
            )
            
            # Update session with results
            session.generated_title = result.get('title', '')
            session.generated_bullets = result.get('bullets', [])
            session.status = 'COMPLETED'
            session.save()
            
        except NotImplementedError:
            # Service not yet implemented
            session.status = 'FAILED'
            session.save()
            return Response(
                {
                    'error': 'AI tailoring service not yet implemented.',
                    'session_id': session.id,
                    'message': 'Session created but AI workflow needs implementation in tailoring/services.py'
                },
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        except Exception as e:
            # Handle other errors
            session.status = 'FAILED'
            session.save()
            return Response(
                {'error': f'Tailoring failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return completed session
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """
        Restart a tailoring session.
        
        POST /api/tailoring/{id}/restart/
        
        Creates a new session with the same job and current experience graph.
        """
        # Get original session
        original_session = self.get_object()
        
        # Check token quota
        try:
            check_and_increment_tokens(request.user, cost=1)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get current experience graph
        try:
            experience_graph = ExperienceGraph.objects.get(user=request.user)
            experience_data = experience_graph.graph_json
        except ExperienceGraph.DoesNotExist:
            return Response(
                {'error': 'Experience graph not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new session
        new_session = TailoringSession.objects.create(
            user=request.user,
            job=original_session.job,
            input_experience_snapshot=experience_data,
            status='PROCESSING',
        )
        
        # Call AgentKit service
        try:
            service = AgentKitTailoringService()
            job = original_session.job
            
            job_description = job.raw_description
            if not job_description and job.source_url:
                job_description = f"[URL to scrape: {job.source_url}]"
            
            result = service.run_workflow(
                job_description=job_description,
                experience_graph=experience_data
            )
            
            new_session.generated_title = result.get('title', '')
            new_session.generated_bullets = result.get('bullets', [])
            new_session.status = 'COMPLETED'
            new_session.save()
            
        except NotImplementedError:
            new_session.status = 'FAILED'
            new_session.save()
            return Response(
                {
                    'error': 'AI tailoring service not yet implemented.',
                    'session_id': new_session.id,
                },
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        except Exception as e:
            new_session.status = 'FAILED'
            new_session.save()
            return Response(
                {'error': f'Tailoring failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = self.get_serializer(new_session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
