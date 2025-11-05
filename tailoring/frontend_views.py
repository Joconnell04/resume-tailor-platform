"""
Frontend views for tailoring app.
"""
import logging
from copy import deepcopy
from datetime import timedelta

from celery.exceptions import OperationalError as CeleryOperationalError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from kombu.exceptions import OperationalError as KombuOperationalError

from experience.models import ExperienceGraph
from jobs.models import JobPosting
from .models import TailoringSession
from .services import AgentKitTailoringService
from .tasks import process_tailoring_session

logger = logging.getLogger(__name__)


@login_required
def tailoring_list(request):
    """List all tailoring sessions for the user."""
    sessions = list(
        TailoringSession.objects.filter(user=request.user).order_by('-created_at')
    )

    refreshed = []
    for session in sessions:
        if _rescue_stuck_session(session):
            session.refresh_from_db()
        refreshed.append(session)

    return render(request, 'tailoring/list.html', {'sessions': refreshed})


@login_required
def tailoring_detail(request, session_id):
    """Display tailoring session details."""
    session = get_object_or_404(TailoringSession, id=session_id, user=request.user)
    if _rescue_stuck_session(session):
        session.refresh_from_db()
    context = {'session': session}
    return render(request, 'tailoring/detail.html', context)


@login_required
def tailoring_create(request):
    """Create a new tailoring session."""
    jobs = JobPosting.objects.filter(user=request.user).order_by('-created_at')
    tone_presets = {
        'confident': {
            'label': 'Confident & Metric-Driven',
            'value': 'confident and metric-driven',
        },
        'impactful': {
            'label': 'Impact-Focused Leadership',
            'value': 'impact-focused and leadership-driven',
        },
        'technical': {
            'label': 'Technical & Detail-Oriented',
            'value': 'technical and detail-oriented',
        },
        'consultative': {
            'label': 'Consultative & Client-Focused',
            'value': 'consultative and client-focused',
        },
    }
    
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        
        if not job_id:
            messages.error(request, 'Please select a job.')
            return redirect('tailoring_create')
        
        job = get_object_or_404(JobPosting, id=job_id, user=request.user)
        
        # Check if user has tokens
        if request.user.tokens_available <= 0:
            messages.error(request, 'Insufficient tokens. Please contact admin.')
            return redirect('tailoring_list')
        
        # Create session
        experience_snapshot = {}
        try:
            experience_snapshot = ExperienceGraph.objects.get(user=request.user).graph_json
        except ExperienceGraph.DoesNotExist:
            experience_snapshot = {}

        job_snapshot = {
            'title': job.title,
            'company': job.company,
            'source_url': job.source_url,
            'raw_description': job.raw_description,
            'location_text': job.location_text,
        }

        sections_input = (request.POST.get('sections') or '').strip()
        sections = [line.strip() for line in sections_input.splitlines() if line.strip()]

        tone_key = request.POST.get('tone_preset', 'confident')
        tone_value = tone_presets.get(tone_key, tone_presets['confident'])['value']
        if tone_key == 'custom':
            tone_value = (request.POST.get('tone_custom') or '').strip() or tone_value

        parameters_raw = {
            'sections': sections,
            'bullets_per_section': request.POST.get('bullets_per_section', '').strip(),
            'tone': tone_value,
            'temperature': request.POST.get('temperature', '').strip(),
            'max_output_tokens': request.POST.get('max_output_tokens', '').strip(),
            'include_summary': request.POST.get('include_summary') == 'on',
            'include_cover_letter': request.POST.get('include_cover_letter') == 'on',
        }

        parameters = AgentKitTailoringService.normalize_parameters(parameters_raw)

        session = TailoringSession.objects.create(
            user=request.user,
            job=job,
            status=TailoringSession.Status.PENDING,
            input_experience_snapshot=experience_snapshot,
            job_snapshot=job_snapshot,
            parameters=parameters,
        )
        
        messages.success(request, f'Tailoring session created for "{job.title}".')
        messages.warning(
            request,
            'AI automation will run shortly. You can monitor progress on the session detail page.'
        )
        try:
            process_tailoring_session.delay(session.id)
        except (KombuOperationalError, CeleryOperationalError, ConnectionError):
            process_tailoring_session.apply(args=(session.id,), throw=True)
            messages.info(
                request,
                'Background queue unavailable, so tailoring ran immediately.'
            )
        except Exception as exc:  # noqa: BLE001
            _mark_session_failed(session, f'Failed to dispatch tailoring task: {exc}')
            messages.error(
                request,
                'We could not start the tailoring run. Please try again shortly.'
            )
        return redirect('tailoring_detail', session_id=session.id)
    
    default_parameters = AgentKitTailoringService.normalize_parameters(
        deepcopy(AgentKitTailoringService.DEFAULT_PARAMETERS)
    )
    default_sections_text = "\n".join(default_parameters['sections'])

    context = {
        'jobs': jobs,
        'default_parameters': default_parameters,
        'tone_presets': tone_presets,
        'default_sections_text': default_sections_text,
    }
    return render(request, 'tailoring/create.html', context)


def _rescue_stuck_session(session: TailoringSession) -> bool:
    """
    Detect pending/processing sessions that exceeded their SLA and attempt recovery.
    Returns True if the session was mutated.
    """
    now = timezone.now()
    mutated = False

    pending_timeout = timedelta(minutes=settings.TAILORING_PENDING_TIMEOUT_MINUTES)
    processing_timeout = timedelta(minutes=settings.TAILORING_PROCESSING_TIMEOUT_MINUTES)

    if (
        session.status == TailoringSession.Status.PENDING
        and now - session.created_at > pending_timeout
    ):
        try:
            logger.warning(
                "Re-attempting stale tailoring session %s for user %s",
                session.id,
                session.user_id,
            )
            process_tailoring_session.apply(args=(session.id,), throw=True)
            mutated = True
        except Exception as exc:  # noqa: BLE001
            logger.error("Tailoring session %s failed to start: %s", session.id, exc)
            _mark_session_failed(
                session,
                "Session could not start in time. Please retry.",
                append_debug=str(exc),
            )
            mutated = True

    elif (
        session.status == TailoringSession.Status.PROCESSING
        and now - session.updated_at > processing_timeout
    ):
        logger.error(
            "Tailoring session %s exceeded processing timeout.", session.id
        )
        _mark_session_failed(
            session,
            "Session exceeded the processing time limit. Please try again.",
        )
        mutated = True

    return mutated


def _mark_session_failed(
    session: TailoringSession,
    message: str,
    *,
    append_debug: str | None = None,
) -> None:
    """
    Persist failure state and audit message to a session.
    """
    session.status = TailoringSession.Status.FAILED
    session.error_message = message
    session.completed_at = timezone.now()
    if append_debug:
        debug_log = session.debug_log or ""
        debug_log += f"\n[{session.completed_at.isoformat()}] {append_debug}"
        session.debug_log = debug_log.strip()
    session.save(
        update_fields=[
            'status',
            'error_message',
            'completed_at',
            'debug_log',
            'updated_at',
        ]
    )
