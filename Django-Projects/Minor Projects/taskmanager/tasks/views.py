from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Task

from django.utils import timezone

def index(request):
    # Get active tasks (not completed) ordered by creation date (newest first)
    active_tasks = Task.objects.filter(completed=False).order_by('-created')
    
    # Get completed tasks (ordered by completion date, most recent first)
    completed_tasks = Task.objects.filter(completed=True).order_by('-updated')
    
    context = {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'active_tasks_count': active_tasks.count(),
        'completed_tasks_count': completed_tasks.count(),
        'today': timezone.localdate(),
    }
    return render(request, 'tasks/index.html', context)

@require_http_methods(["POST"])
def add_task(request):
    title = request.POST.get('title')
    details = request.POST.get('details', '').strip() or None
    due_date_str = request.POST.get('due_date')
    
    if title:
        task = Task(title=title, details=details)
        if due_date_str:
            from datetime import datetime
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass  # If date format is invalid, just don't set it
        task.save()
    return redirect('tasks:index')

def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.completed = not task.completed
    task.save()
    return redirect('tasks:index')

def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return redirect('tasks:index')
