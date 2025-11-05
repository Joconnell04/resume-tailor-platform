"""
Frontend views for jobs app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobPosting


@login_required
def job_list(request):
    """List all jobs for the user."""
    jobs = JobPosting.objects.filter(user=request.user).order_by('-created_at')
    context = {'jobs': jobs}
    return render(request, 'jobs/list.html', context)


@login_required
def job_detail(request, job_id):
    """Display job details."""
    job = get_object_or_404(JobPosting, id=job_id, user=request.user)
    context = {'job': job}
    return render(request, 'jobs/detail.html', context)


@login_required
def job_create(request):
    """Create a new job posting."""
    if request.method == 'POST':
        title = request.POST.get('title')
        company = request.POST.get('company')
        raw_description = request.POST.get('raw_description')
        location_text = request.POST.get('location_text', '')
        url = request.POST.get('url', '')
        
        job = JobPosting.objects.create(
            user=request.user,
            title=title,
            company=company,
            raw_description=raw_description,
            location_text=location_text,
            url=url
        )
        messages.success(request, f'Job "{title}" created successfully.')
        return redirect('job_detail', job_id=job.id)
    
    return render(request, 'jobs/create.html')


@login_required
def job_edit(request, job_id):
    """Edit an existing job posting."""
    job = get_object_or_404(JobPosting, id=job_id, user=request.user)
    
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.raw_description = request.POST.get('raw_description')
        job.location_text = request.POST.get('location_text', '')
        job.url = request.POST.get('url', '')
        job.save()
        
        messages.success(request, f'Job "{job.title}" updated successfully.')
        return redirect('job_detail', job_id=job.id)
    
    context = {'job': job}
    return render(request, 'jobs/edit.html', context)


@login_required
def job_delete(request, job_id):
    """Delete a job posting."""
    job = get_object_or_404(JobPosting, id=job_id, user=request.user)
    
    if request.method == 'POST':
        title = job.title
        job.delete()
        messages.success(request, f'Job "{title}" deleted successfully.')
        return redirect('job_list')
    
    context = {'job': job}
    return render(request, 'jobs/delete.html', context)
