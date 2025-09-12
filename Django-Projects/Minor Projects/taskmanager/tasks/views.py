from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from .models import Task
from datetime import datetime, date
from typing import TYPE_CHECKING, Union, Optional, cast

from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

# Create a custom HttpRequest type with user attribute
class AuthenticatedHttpRequest(HttpRequest):
    user: Union[User, 'AnonymousUser']

# Authentication Views
def register_view(request: AuthenticatedHttpRequest) -> HttpResponse:
    if hasattr(request, 'user') and request.user.is_authenticated:
        return redirect('tasks:index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Ensure we have strings
        username = str(username) if username else ''
        email = str(email) if email else ''
        password = str(password) if password else ''
        confirm_password = str(confirm_password) if confirm_password else ''
        
        # Basic validation
        if not all([username, email, password, confirm_password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'auth/register.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'auth/register.html')
        
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'auth/register.html')
        
        if '@' not in str(email) or '.' not in str(email):
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'auth/register.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('tasks:login')
        except IntegrityError:
            messages.error(request, 'Username already exists. Please choose a different one.')
            return render(request, 'auth/register.html')
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'auth/register.html')
    
    return render(request, 'auth/register.html')

def login_view(request: AuthenticatedHttpRequest) -> HttpResponse:
    if hasattr(request, 'user') and request.user.is_authenticated:
        return redirect('tasks:index')
    
    if request.method == 'POST':
        username = str(request.POST.get('username', ''))
        password = str(request.POST.get('password', ''))
        
        if not all([username, password]):
            messages.error(request, 'Both username and password are required.')
            return render(request, 'auth/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('tasks:index')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'auth/login.html')
    
    return render(request, 'auth/login.html')

def logout_view(request: AuthenticatedHttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('tasks:login')

# Task Views

# Task Views
@login_required
def index(request: AuthenticatedHttpRequest) -> HttpResponse:
    # Get active tasks (not completed) for the current user ordered by creation date (newest first)
    user = request.user  # type: ignore
    active_tasks = Task.objects.filter(user=user, completed=False).order_by('-created')  # type: ignore
    
    # Get completed tasks for the current user (ordered by completion date, most recent first)
    completed_tasks = Task.objects.filter(user=user, completed=True).order_by('-updated')  # type: ignore
    
    context = {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'active_tasks_count': active_tasks.count(),
        'completed_tasks_count': completed_tasks.count(),
        'today': timezone.localdate(),
    }
    return render(request, 'tasks/index.html', context)

@require_http_methods(["POST"])
@login_required
def add_task(request: AuthenticatedHttpRequest) -> HttpResponse:
    title_raw = request.POST.get('title', '')
    details_raw = request.POST.get('details', '')
    due_date_raw = request.POST.get('due_date', '')
    
    # Ensure we have strings and strip them
    title = str(title_raw).strip() if title_raw else ''
    details = str(details_raw).strip() if details_raw else ''
    due_date_str = str(due_date_raw).strip() if due_date_raw else ''
    
    details = details or None  # Convert empty string to None
    
    if title and len(title) >= 3:
        user = request.user  # type: ignore
        task = Task(title=title, details=details, user=user)
        if due_date_str:
            try:
                parsed_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                # Ensure due date is not in the past
                if parsed_date >= timezone.localdate():
                    task.due_date = parsed_date  # type: ignore
                else:
                    messages.warning(request, 'Due date cannot be in the past. Task created without due date.')
            except (ValueError, TypeError):
                messages.warning(request, 'Invalid date format. Task created without due date.')
        task.save()
        messages.success(request, 'Task added successfully!')
    elif not title:
        messages.error(request, 'Task title is required.')
    else:
        messages.error(request, 'Task title must be at least 3 characters long.')
    return redirect('tasks:index')

@login_required
def toggle_task(request: AuthenticatedHttpRequest, task_id: int) -> HttpResponse:
    try:
        user = request.user  # type: ignore
        task = get_object_or_404(Task, id=task_id, user=user)
        task.completed = not task.completed
        task.save()
        status_msg = 'completed' if task.completed else 'marked as active'
        messages.success(request, f'Task "{task.title}" {status_msg}!')
    except Exception as e:
        messages.error(request, 'Error updating task. Please try again.')
    return redirect('tasks:index')

@login_required
def delete_task(request: AuthenticatedHttpRequest, task_id: int) -> HttpResponse:
    try:
        user = request.user  # type: ignore
        task = get_object_or_404(Task, id=task_id, user=user)
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
    except Exception as e:
        messages.error(request, 'Error deleting task. Please try again.')
    return redirect('tasks:index')
