"""
Frontend views for experience app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ExperienceGraph
import json


@login_required
def experience_list(request):
    """Display user's experience graph."""
    try:
        experience = ExperienceGraph.objects.get(user=request.user)
        graph_data = experience.graph_json
    except ExperienceGraph.DoesNotExist:
        experience = None
        graph_data = None
    
    context = {
        'experience': experience,
        'graph_data': json.dumps(graph_data, indent=2) if graph_data else None,
    }
    return render(request, 'experience/list.html', context)


@login_required
def experience_create(request):
    """Create or update experience graph."""
    if request.method == 'POST':
        graph_json_str = request.POST.get('graph_json')
        try:
            graph_json = json.loads(graph_json_str)
            experience, created = ExperienceGraph.objects.update_or_create(
                user=request.user,
                defaults={'graph_json': graph_json}
            )
            action = 'created' if created else 'updated'
            messages.success(request, f'Experience graph {action} successfully.')
            return redirect('experience_list')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'experience/create.html')


@login_required
def experience_edit(request):
    """Edit existing experience graph."""
    try:
        experience = ExperienceGraph.objects.get(user=request.user)
        initial_data = json.dumps(experience.graph_json, indent=2)
    except ExperienceGraph.DoesNotExist:
        messages.warning(request, 'No experience graph found. Creating new one.')
        return redirect('experience_create')
    
    if request.method == 'POST':
        graph_json_str = request.POST.get('graph_json')
        try:
            graph_json = json.loads(graph_json_str)
            experience.graph_json = graph_json
            experience.save()
            messages.success(request, 'Experience graph updated successfully.')
            return redirect('experience_list')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON format.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'experience': experience,
        'initial_data': initial_data,
    }
    return render(request, 'experience/edit.html', context)
