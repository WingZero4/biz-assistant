from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from onboarding.models import GeneratedDocument, WeeklyPulse
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from onboarding.chat_service import ChatService
from onboarding.document_service import DocumentService
from onboarding.forms import DocumentGenerationForm, WeeklyPulseForm
from tasks.achievement_service import AchievementService
from tasks.analytics_service import AnalyticsService
from tasks.models import Task, TaskPlan
from tasks.services import TaskGenerationService

from .forms import ProfileForm, SignupForm


def _get_monday(date):
    """Return the Monday of the week containing the given date."""
    return date - timezone.timedelta(days=date.weekday())


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

    # Achievements & streak
    current_streak = AchievementService.get_current_streak(request.user)
    recent_achievements = AchievementService.get_user_achievements(
        request.user,
    )[:5]

    # Weekly pulse check-in prompt
    this_monday = _get_monday(today)
    pulse_done_this_week = WeeklyPulse.objects.filter(
        user=request.user, week_of=this_monday,
    ).exists()

    # Plan continuation detection
    continuation = TaskGenerationService.detect_plan_ready_for_continuation(request.user)

    return render(request, 'dashboard/home.html', {
        'plan': active_plan,
        'today_tasks': today_tasks,
        'recent_completed': recent_completed,
        'upcoming_tasks': upcoming_tasks,
        'today': today,
        'stats': stats,
        'current_streak': current_streak,
        'recent_achievements': recent_achievements,
        'pulse_done_this_week': pulse_done_this_week,
        'continuation': continuation,
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


@login_required
def weekly_pulse_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    today = timezone.now().date()
    this_monday = _get_monday(today)
    profile = request.user.business_profile

    # Get or pre-fill existing pulse for this week
    existing = WeeklyPulse.objects.filter(
        user=request.user, week_of=this_monday,
    ).first()

    if request.method == 'POST':
        form = WeeklyPulseForm(request.POST, instance=existing)
        if form.is_valid():
            pulse = form.save(commit=False)
            pulse.user = request.user
            pulse.business_profile = profile
            pulse.week_of = this_monday
            pulse.save()
            messages.success(request, 'Weekly check-in saved!')
            return redirect('accounts:dashboard')
    else:
        form = WeeklyPulseForm(instance=existing)

    return render(request, 'dashboard/pulse.html', {
        'form': form,
        'week_of': this_monday,
        'is_update': existing is not None,
    })


@login_required
def pulse_history_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    pulses = WeeklyPulse.objects.filter(user=request.user)

    return render(request, 'dashboard/pulse_history.html', {
        'pulses': pulses,
    })


@login_required
def analytics_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    user = request.user
    summary = AnalyticsService.get_summary_stats(user)
    weekly_trend = AnalyticsService.get_weekly_completion_trend(user)
    category_breakdown = AnalyticsService.get_category_breakdown(user)
    time_invested = AnalyticsService.get_time_invested(user)
    plan_comparison = AnalyticsService.get_plan_comparison(user)
    streak_history = AnalyticsService.get_streak_history(user)
    pulse_trends = AnalyticsService.get_pulse_trends(user)

    chart_data = {
        'weekly_trend': weekly_trend,
        'category_breakdown': category_breakdown,
        'time_invested': time_invested,
        'streak_history': streak_history,
        'pulse_trends': pulse_trends,
    }

    return render(request, 'dashboard/analytics.html', {
        'summary': summary,
        'plan_comparison': plan_comparison,
        'chart_data_json': json.dumps(chart_data),
    })


@login_required
def chat_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    session_id = ChatService.get_or_create_session(request.user)
    history = ChatService.get_chat_history(request.user, session_id)

    return render(request, 'dashboard/chat.html', {
        'history': history,
        'session_id': session_id,
    })


@login_required
@require_POST
def chat_send_view(request):
    """AJAX endpoint — send message and get AI response."""
    if not request.user.profile.is_onboarded:
        return JsonResponse({'error': 'Not onboarded'}, status=403)

    user_message = request.POST.get('message', '').strip()
    session_id = request.POST.get('session_id', '')

    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)
    if len(user_message) > 5000:
        return JsonResponse({'error': 'Message too long (max 5000 characters)'}, status=400)
    if not session_id:
        return JsonResponse({'error': 'Session ID is required'}, status=400)

    response = ChatService.send_message(request.user, session_id, user_message)

    return JsonResponse({
        'reply': response.content,
        'created_at': response.created_at.isoformat(),
    })


@login_required
@require_POST
def chat_new_session_view(request):
    """Start a fresh chat session."""
    session_id = ChatService.start_new_session(request.user)
    return redirect('accounts:chat')


@login_required
def documents_view(request):
    if not request.user.profile.is_onboarded:
        return redirect('onboarding:step_1')

    form = DocumentGenerationForm()
    documents = DocumentService.get_user_documents(request.user)

    return render(request, 'dashboard/documents.html', {
        'form': form,
        'documents': documents,
    })


@login_required
@require_POST
def document_generate_view(request):
    """AJAX endpoint — generate a document."""
    if not request.user.profile.is_onboarded:
        return JsonResponse({'error': 'Not onboarded'}, status=403)

    form = DocumentGenerationForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form data'}, status=400)

    doc = DocumentService.generate_document(
        user=request.user,
        doc_type=form.cleaned_data['doc_type'],
        topic=form.cleaned_data['topic'],
        platform=form.cleaned_data.get('platform', ''),
        notes=form.cleaned_data.get('notes', ''),
    )

    return JsonResponse({
        'id': doc.pk,
        'title': doc.title,
        'content': doc.content,
        'doc_type': doc.get_doc_type_display(),
        'created_at': doc.created_at.isoformat(),
    })


@login_required
@require_POST
def document_favorite_view(request, pk):
    """Toggle favorite status of a document."""
    document = get_object_or_404(GeneratedDocument, pk=pk, user=request.user)
    DocumentService.toggle_favorite(document)
    return redirect('accounts:documents')
