from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import Task, TaskPlan
from .services import TaskProgressService


@login_required
def task_list_view(request):
    active_plan = TaskPlan.objects.filter(
        user=request.user, status='ACTIVE',
    ).first()

    tasks = Task.objects.none()
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')

    if active_plan:
        tasks = active_plan.tasks.all()
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        if category_filter:
            tasks = tasks.filter(category=category_filter)

    return render(request, 'dashboard/task_list.html', {
        'plan': active_plan,
        'tasks': tasks,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'status_choices': Task.STATUS_CHOICES,
        'category_choices': Task.CATEGORY_CHOICES,
    })


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, pk=pk, plan__user=request.user)
    return render(request, 'dashboard/task_detail.html', {'task': task})


@login_required
def mark_done_view(request, pk):
    if request.method != 'POST':
        return redirect('tasks:list')

    task = get_object_or_404(Task, pk=pk, plan__user=request.user)
    try:
        TaskProgressService.mark_done(task)
        messages.success(request, f'"{task.title}" marked as done!')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(request.POST.get('next', 'accounts:dashboard'))


@login_required
def mark_skip_view(request, pk):
    if request.method != 'POST':
        return redirect('tasks:list')

    task = get_object_or_404(Task, pk=pk, plan__user=request.user)
    try:
        TaskProgressService.mark_skipped(task)
        messages.info(request, f'"{task.title}" skipped.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(request.POST.get('next', 'accounts:dashboard'))
