"""Analytics service — computes dashboard data from existing models."""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from onboarding.models import WeeklyPulse

from .models import StreakRecord, Task, TaskPlan


class AnalyticsService:

    @staticmethod
    def get_weekly_completion_trend(user, weeks=8):
        """Weekly task completion rates over the last N weeks."""
        today = timezone.now().date()
        # Start from the most recent Monday
        current_monday = today - timedelta(days=today.weekday())
        trend = []

        for i in range(weeks - 1, -1, -1):
            week_start = current_monday - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)

            tasks = Task.objects.filter(
                plan__user=user,
                due_date__gte=week_start,
                due_date__lte=week_end,
            )
            total = tasks.count()
            completed = tasks.filter(status='DONE').count()
            rate = round((completed / total) * 100) if total > 0 else 0

            trend.append({
                'week_of': week_start.isoformat(),
                'label': week_start.strftime('%b %d'),
                'completed': completed,
                'total': total,
                'rate': rate,
            })

        return trend

    @staticmethod
    def get_category_breakdown(user, plan=None):
        """Task completion by category."""
        qs = Task.objects.filter(plan__user=user)
        if plan:
            qs = qs.filter(plan=plan)

        categories = qs.values('category').annotate(
            total=Count('id'),
            done=Count('id', filter=Q(status='DONE')),
        ).order_by('category')

        result = []
        cat_labels = dict(Task.CATEGORY_CHOICES)
        for cat in categories:
            total = cat['total']
            done = cat['done']
            result.append({
                'category': cat['category'],
                'label': cat_labels.get(cat['category'], cat['category']),
                'done': done,
                'total': total,
                'pct': round((done / total) * 100) if total > 0 else 0,
            })

        return result

    @staticmethod
    def get_time_invested(user, plan=None):
        """Total estimated time invested (from completed tasks)."""
        qs = Task.objects.filter(plan__user=user, status='DONE')
        if plan:
            qs = qs.filter(plan=plan)

        total_minutes = qs.aggregate(total=Sum('estimated_minutes'))['total'] or 0

        by_category = {}
        cat_data = qs.values('category').annotate(mins=Sum('estimated_minutes'))
        cat_labels = dict(Task.CATEGORY_CHOICES)
        for item in cat_data:
            by_category[cat_labels.get(item['category'], item['category'])] = item['mins']

        return {
            'total_minutes': total_minutes,
            'total_hours': round(total_minutes / 60, 1),
            'by_category': by_category,
        }

    @staticmethod
    def get_plan_comparison(user):
        """Compare completion rates across plans."""
        plans = TaskPlan.objects.filter(user=user).order_by('created_at')
        result = []
        for plan in plans:
            result.append({
                'title': plan.title,
                'phase': plan.phase,
                'status': plan.status,
                'completion_pct': plan.completion_pct,
                'starts_on': plan.starts_on.isoformat(),
                'ends_on': plan.ends_on.isoformat(),
            })
        return result

    @staticmethod
    def get_streak_history(user, days=30):
        """Daily streak data for heatmap."""
        today = timezone.now().date()
        start = today - timedelta(days=days - 1)

        records = {
            r.date: r.tasks_completed
            for r in StreakRecord.objects.filter(
                user=user, date__gte=start,
            )
        }

        history = []
        for i in range(days):
            date = start + timedelta(days=i)
            history.append({
                'date': date.isoformat(),
                'label': date.strftime('%b %d'),
                'day_name': date.strftime('%a'),
                'tasks_completed': records.get(date, 0),
            })

        return history

    @staticmethod
    def get_pulse_trends(user, weeks=12):
        """Weekly pulse trends for charts."""
        pulses = WeeklyPulse.objects.filter(
            user=user,
        ).order_by('week_of')[:weeks]

        revenue = []
        customers = []
        energy = []
        hours = []

        for p in pulses:
            label = p.week_of.strftime('%b %d')
            revenue.append({
                'week': label,
                'value': float(p.revenue_this_week) if p.revenue_this_week else 0,
            })
            customers.append({'week': label, 'value': p.new_customers})
            energy.append({'week': label, 'value': p.energy_level})
            hours.append({'week': label, 'value': p.hours_worked})

        return {
            'revenue': revenue,
            'customers': customers,
            'energy': energy,
            'hours': hours,
        }

    @staticmethod
    def get_summary_stats(user):
        """Top-level summary numbers for the analytics page."""
        from .achievement_service import AchievementService

        done_count = Task.objects.filter(plan__user=user, status='DONE').count()
        total_count = Task.objects.filter(plan__user=user).count()
        time_data = AnalyticsService.get_time_invested(user)
        current_streak = AchievementService.get_current_streak(user)
        avg_rate = round((done_count / total_count) * 100) if total_count > 0 else 0

        return {
            'tasks_completed': done_count,
            'total_tasks': total_count,
            'hours_invested': time_data['total_hours'],
            'current_streak': current_streak,
            'avg_completion_rate': avg_rate,
        }
