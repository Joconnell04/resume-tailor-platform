"""
Frontend views for tailoring app.
"""
import logging
import threading
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
    
    # Auto-start processing if still pending and hasn't been attempted yet
    if session.status == TailoringSession.Status.PENDING:
        try:
            # Dispatch in background thread to avoid blocking the response
            thread = threading.Thread(
                target=_run_task_in_background,
                args=(session.id,),
                daemon=True
            )
            thread.start()
            logger.info(f"Started background thread for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to start background thread for session {session_id}: {e}")
    
    if _rescue_stuck_session(session):
        session.refresh_from_db()
    
    context = {'session': session}
    return render(request, 'tailoring/detail.html', context)


@login_required
def tailoring_create(request):
    """Create a new tailoring session."""
    jobs = JobPosting.objects.filter(user=request.user).order_by('-created_at')

    # Get pre-selected job from query parameter
    preselected_job_id = request.GET.get('job_id')
    preselected_job = None
    if preselected_job_id:
        try:
            preselected_job = JobPosting.objects.get(id=preselected_job_id, user=request.user)
        except JobPosting.DoesNotExist:
            pass

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
        
        # Get section order if provided
        sections_order = (request.POST.get('sections_order') or '').strip()
        if sections_order:
            ordered_sections = [s.strip() for s in sections_order.split(',') if s.strip()]
            # Use ordered sections if provided, otherwise use default order
            if ordered_sections:
                sections = ordered_sections
        
        # Get custom instructions
        section_instructions = (request.POST.get('section_instructions') or '').strip()

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
            'section_instructions': section_instructions,
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
        messages.info(
            request,
            'Processing has started. This page will auto-refresh to show progress.'
        )
        
        # Redirect FIRST before starting any processing
        # The detail page will handle dispatching the task if it hasn't started yet
        return redirect('tailoring_detail', session_id=session.id)
    
    default_parameters = AgentKitTailoringService.normalize_parameters(
        deepcopy(AgentKitTailoringService.DEFAULT_PARAMETERS)
    )
    default_sections_text = "\n".join(default_parameters['sections'])

    context = {
        'jobs': jobs,
        'preselected_job': preselected_job,
        'default_parameters': default_parameters,
        'tone_presets': tone_presets,
        'default_sections_text': default_sections_text,
    }
    return render(request, 'tailoring/create.html', context)


@login_required
def tailoring_delete(request, session_id):
    """Delete a tailoring session owned by the current user."""
    session = get_object_or_404(TailoringSession, id=session_id, user=request.user)
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Tailoring session deleted.')
        return redirect('tailoring_list')
    messages.error(request, 'Invalid request.')
    return redirect('tailoring_detail', session_id=session_id)


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
            _dispatch_tailoring_task(session, allow_inline=True)
            mutated = True
        except Exception:
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


def _run_task_in_background(session_id: int) -> None:
    """
    Run the tailoring task in a background thread.
    This function attempts Celery first, then falls back to direct execution.
    """
    try:
        # Try to dispatch via Celery
        process_tailoring_session.delay(session_id)
        logger.info(f"Queued session {session_id} via Celery")
    except (KombuOperationalError, CeleryOperationalError, ConnectionError) as e:
        # Celery/Redis not available - run directly
        logger.warning(f"Queue unavailable for session {session_id}, running inline: {e}")
        try:
            process_tailoring_session(session_id)
            logger.info(f"Completed session {session_id} inline")
        except Exception as inline_exc:
            logger.error(f"Inline execution failed for session {session_id}: {inline_exc}")
    except Exception as e:
        logger.error(f"Unexpected error dispatching session {session_id}: {e}")


def _dispatch_tailoring_task(
    session: TailoringSession,
    *,
    request=None,
    allow_inline: bool = True,
) -> str:
    """
    Try to enqueue the tailoring task. Falls back to inline execution when possible.

    Returns:
        "queued" if the task was enqueued, "inline" if executed immediately.
    """
    try:
        process_tailoring_session.delay(session.id)
        return "queued"
    except (KombuOperationalError, CeleryOperationalError, ConnectionError) as exc:
        logger.warning(
            "Queue unavailable for session %s. Falling back to inline execution. %s",
            session.id,
            exc,
        )
        if allow_inline:
            try:
                process_tailoring_session.apply(args=(session.id,), throw=True)
                if request:
                    messages.info(
                        request,
                        'Queue is offline, so tailoring ran immediately.',
                    )
                return "inline"
            except Exception as inline_exc:  # noqa: BLE001
                _mark_session_failed(
                    session,
                    "Tailoring session could not run because the queue is unavailable.",
                    append_debug=str(inline_exc),
                )
                raise inline_exc

        _mark_session_failed(
            session,
            "Tailoring session could not be queued.",
            append_debug=str(exc),
        )
        raise exc
    except Exception as exc:  # noqa: BLE001
        _mark_session_failed(
            session,
            "Unexpected error when starting tailoring session.",
            append_debug=str(exc),
        )
        raise exc


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
