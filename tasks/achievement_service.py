"""Achievement & streak tracking service."""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from .models import Achievement, StreakRecord, Task, TaskPlan


class AchievementService:

    @staticmethod
    def record_task_completion(task: Task) -> list[Achievement]:
        """Called after a task is marked DONE. Records streak and checks badges."""
        user = task.plan.user
        today = timezone.now().date()

        # Update or create today's streak record
        record, _ = StreakRecord.objects.get_or_create(
            user=user, date=today,
            defaults={'tasks_completed': 0},
        )
        record.tasks_completed += 1
        record.save(update_fields=['tasks_completed'])

        # Check all badge types
        new_badges = []
        new_badges.extend(AchievementService._check_milestone_badges(user, task))
        new_badges.extend(AchievementService._check_streak_badges(user))
        new_badges.extend(AchievementService._check_special_badges(user, task))
        return new_badges

    @staticmethod
    def _check_milestone_badges(user, task) -> list[Achievement]:
        """Check for completion-count milestones."""
        badges = []
        plan = task.plan
        done_count = plan.tasks.filter(status='DONE').count()
        total_count = plan.tasks.count()

        # First task ever
        total_done_all_plans = Task.objects.filter(
            plan__user=user, status='DONE',
        ).count()
        if total_done_all_plans == 1:
            badges.append(AchievementService._award(
                user, 'FIRST_TASK', 'First Task Completed',
                'You completed your very first task!',
            ))

        # Halfway through plan
        halfway = (total_count + 1) // 2
        if total_count > 0 and done_count >= halfway and done_count > 0:
            if not Achievement.objects.filter(
                user=user, badge='HALF_PLAN',
                metadata__plan_id=plan.pk,
            ).exists():
                badges.append(AchievementService._award(
                    user, 'HALF_PLAN', 'Halfway There',
                    f'You\'re halfway through "{plan.title}"!',
                    metadata={'plan_id': plan.pk},
                ))

        # Plan complete
        if total_count > 0 and done_count == total_count:
            if not Achievement.objects.filter(
                user=user, badge='PLAN_COMPLETE',
                metadata__plan_id=plan.pk,
            ).exists():
                badges.append(AchievementService._award(
                    user, 'PLAN_COMPLETE', 'Plan Completed',
                    f'You completed every task in "{plan.title}"!',
                    metadata={'plan_id': plan.pk},
                ))

        # Category master — all tasks in a category done
        category = task.category
        cat_tasks = plan.tasks.filter(category=category)
        if cat_tasks.count() >= 3 and cat_tasks.filter(status='DONE').count() == cat_tasks.count():
            if not Achievement.objects.filter(
                user=user, badge='CATEGORY_MASTER',
                metadata__category=category,
                metadata__plan_id=plan.pk,
            ).exists():
                cat_label = dict(Task.CATEGORY_CHOICES).get(category, category)
                badges.append(AchievementService._award(
                    user, 'CATEGORY_MASTER', f'{cat_label} Master',
                    f'You completed all {cat_label} tasks!',
                    metadata={'category': category, 'plan_id': plan.pk},
                ))

        return badges

    @staticmethod
    def _check_streak_badges(user) -> list[Achievement]:
        """Check for streak-based badges."""
        badges = []
        streak = AchievementService.get_current_streak(user)

        streak_thresholds = [
            (3, 'STREAK_3', '3-Day Streak', '3 days in a row!'),
            (7, 'STREAK_7', '7-Day Streak', 'A full week of consistency!'),
            (14, 'STREAK_14', '14-Day Streak', 'Two weeks strong!'),
            (30, 'STREAK_30', '30-Day Streak', 'An entire month — unstoppable!'),
        ]

        for threshold, badge, title, desc in streak_thresholds:
            if streak >= threshold and not Achievement.objects.filter(
                user=user, badge=badge,
            ).exists():
                badges.append(AchievementService._award(user, badge, title, desc))

        # First week complete (7 days since plan start with >=5 streak records)
        active_plan = TaskPlan.objects.filter(user=user, status='ACTIVE').first()
        if active_plan:
            days_since_start = (timezone.now().date() - active_plan.starts_on).days
            if days_since_start >= 7:
                first_week_records = StreakRecord.objects.filter(
                    user=user,
                    date__gte=active_plan.starts_on,
                    date__lte=active_plan.starts_on + timedelta(days=6),
                ).count()
                if first_week_records >= 5 and not Achievement.objects.filter(
                    user=user, badge='FIRST_WEEK',
                ).exists():
                    badges.append(AchievementService._award(
                        user, 'FIRST_WEEK', 'First Week Complete',
                        'You showed up 5+ days in your first week!',
                    ))

        return badges

    @staticmethod
    def _check_special_badges(user, task) -> list[Achievement]:
        """Check for special achievement badges."""
        badges = []

        # Speed demon — completed a HARD task in under estimated time
        if (
            task.difficulty == 'HARD'
            and task.completed_at
            and task.sent_at
            and (task.completed_at - task.sent_at).total_seconds() < task.estimated_minutes * 60
        ):
            if not Achievement.objects.filter(user=user, badge='SPEED_DEMON').exists():
                badges.append(AchievementService._award(
                    user, 'SPEED_DEMON', 'Speed Demon',
                    'Completed a hard task faster than estimated!',
                ))

        # Comeback kid — completed a task after 3+ day gap
        today = timezone.now().date()
        recent_records = StreakRecord.objects.filter(
            user=user,
            date__lt=today,
        ).order_by('-date')[:1]
        if recent_records.exists():
            last_active = recent_records[0].date
            gap = (today - last_active).days
            if gap >= 3 and not Achievement.objects.filter(
                user=user, badge='COMEBACK',
            ).exists():
                badges.append(AchievementService._award(
                    user, 'COMEBACK', 'Comeback Kid',
                    f'Welcome back after {gap} days!',
                ))

        # Multi-plan veteran — completed tasks in 2+ plans
        plans_with_done = TaskPlan.objects.filter(
            user=user,
            tasks__status='DONE',
        ).distinct().count()
        if plans_with_done >= 2 and not Achievement.objects.filter(
            user=user, badge='MULTI_PLAN',
        ).exists():
            badges.append(AchievementService._award(
                user, 'MULTI_PLAN', 'Multi-Plan Veteran',
                'You\'ve completed tasks across multiple plans!',
            ))

        return badges

    @staticmethod
    def get_current_streak(user) -> int:
        """Count consecutive days (including today) with completed tasks."""
        today = timezone.now().date()
        streak = 0
        check_date = today

        while True:
            exists = StreakRecord.objects.filter(
                user=user, date=check_date,
            ).exists()
            if exists:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return streak

    @staticmethod
    def get_user_achievements(user):
        """Return all achievements for a user."""
        return Achievement.objects.filter(user=user)

    @staticmethod
    def _award(user, badge, title, description, metadata=None) -> Achievement:
        """Create an achievement, avoiding duplicates for non-parameterized badges."""
        return Achievement.objects.create(
            user=user,
            badge=badge,
            title=title,
            description=description,
            metadata=metadata or {},
        )
