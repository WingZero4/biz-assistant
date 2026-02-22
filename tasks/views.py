from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import Task, TaskPlan, TaskResource
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
    resources = task.resources.all()
    return render(request, 'dashboard/task_detail.html', {
        'task': task,
        'resources': resources,
    })


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


@login_required
def reschedule_view(request, pk):
    """Reschedule a task to a future date."""
    if request.method != 'POST':
        return redirect('tasks:detail', pk=pk)

    task = get_object_or_404(Task, pk=pk, plan__user=request.user)
    new_date = request.POST.get('new_date')
    if not new_date:
        messages.error(request, 'Please select a date.')
        return redirect('tasks:detail', pk=pk)

    from datetime import date as date_type
    try:
        parsed = date_type.fromisoformat(new_date)
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect('tasks:detail', pk=pk)

    from django.utils import timezone
    if parsed <= timezone.now().date():
        messages.error(request, 'Reschedule date must be in the future.')
        return redirect('tasks:detail', pk=pk)

    try:
        TaskProgressService.reschedule_task(task, parsed)
        messages.success(request, f'"{task.title}" rescheduled to {parsed}.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('accounts:dashboard')


@login_required
def regenerate_plan_view(request):
    """Regenerate the user's task plan."""
    if request.method != 'POST':
        return redirect('accounts:dashboard')

    from onboarding.models import BusinessProfile
    try:
        profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'Complete onboarding first.')
        return redirect('onboarding:step_1')

    from .services import TaskGenerationService

    # Pause current active plan
    current = TaskPlan.objects.filter(user=request.user, status='ACTIVE').first()
    if current:
        current.status = 'REPLACED'
        current.save(update_fields=['status'])

    plan = TaskGenerationService.generate_plan(profile)
    messages.success(request, f'New plan generated with {plan.tasks.count()} tasks!')
    return redirect('accounts:dashboard')


@login_required
def toggle_resource_view(request, pk):
    """Toggle a checklist resource item's completion status."""
    if request.method != 'POST':
        return redirect('tasks:list')

    resource = get_object_or_404(
        TaskResource, pk=pk, task__plan__user=request.user,
    )
    resource.is_completed = not resource.is_completed
    resource.save(update_fields=['is_completed'])
    return redirect('tasks:detail', pk=resource.task.pk)
