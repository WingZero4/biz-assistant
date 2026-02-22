from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from tasks.models import Task, TaskPlan

from .forms import ProfileForm, SignupForm


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'landing.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('onboarding:step_1')
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    today = timezone.now().date()
    active_plan = TaskPlan.objects.filter(
        user=request.user, status='ACTIVE',
    ).first()

    today_tasks = []
    recent_completed = []
    upcoming_tasks = []
    stats = {}

    if active_plan:
        today_tasks = active_plan.tasks.filter(due_date=today).exclude(
            status__in=['DONE', 'SKIPPED'],
        )
        recent_completed = active_plan.tasks.filter(
            status='DONE',
        ).order_by('-completed_at')[:5]
        upcoming_tasks = active_plan.tasks.filter(
            due_date__gt=today, status='PENDING',
        )[:10]

        total = active_plan.tasks.count()
        done = active_plan.tasks.filter(status='DONE').count()
        skipped = active_plan.tasks.filter(status='SKIPPED').count()
        overdue = active_plan.tasks.filter(
            due_date__lt=today, status__in=['PENDING', 'SENT'],
        ).count()
        stats = {
            'total': total,
            'done': done,
            'skipped': skipped,
            'remaining': total - done - skipped,
            'overdue': overdue,
        }

    return render(request, 'dashboard/home.html', {
        'plan': active_plan,
        'today_tasks': today_tasks,
        'recent_completed': recent_completed,
        'upcoming_tasks': upcoming_tasks,
        'today': today,
        'stats': stats,
    })


@login_required
def assessment_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    profile = request.user.business_profile
    assessment = profile.ai_assessment or {}

    return render(request, 'dashboard/assessment.html', {
        'profile': profile,
        'assessment': assessment,
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'registration/profile.html', {'form': form})
