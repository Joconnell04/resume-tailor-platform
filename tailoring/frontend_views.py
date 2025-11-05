"""
Frontend views for tailoring app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TailoringSession
from jobs.models import JobPosting


@login_required
def tailoring_list(request):
    """List all tailoring sessions for the user."""
    sessions = TailoringSession.objects.filter(user=request.user).order_by('-created_at')
    context = {'sessions': sessions}
    return render(request, 'tailoring/list.html', context)


@login_required
def tailoring_detail(request, session_id):
    """Display tailoring session details."""
    session = get_object_or_404(TailoringSession, id=session_id, user=request.user)
    context = {'session': session}
    return render(request, 'tailoring/detail.html', context)


@login_required
def tailoring_create(request):
    """Create a new tailoring session."""
    jobs = JobPosting.objects.filter(user=request.user).order_by('-created_at')
    
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
        session = TailoringSession.objects.create(
            user=request.user,
            job=job,
            status='pending'
        )
        
        messages.success(request, f'Tailoring session created for "{job.title}".')
        messages.warning(request, 'AI integration not yet implemented. Session is pending.')
        return redirect('tailoring_detail', session_id=session.id)
    
    context = {'jobs': jobs}
    return render(request, 'tailoring/create.html', context)
