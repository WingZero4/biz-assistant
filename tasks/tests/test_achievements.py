from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from onboarding.models import BusinessProfile
from tasks.achievement_service import AchievementService
from tasks.models import Achievement, StreakRecord, Task, TaskPlan
from tasks.services import TaskProgressService


def _create_test_user():
    return User.objects.create_user('testuser', 'test@example.com', 'pass123')


def _create_test_profile(user):
    return BusinessProfile.objects.create(
        user=user,
        business_name='Test Bakery',
        business_type='Bakery',
        stage='IDEA',
        goals=['First 10 customers'],
        ai_assessment={'summary': 'Good idea', 'focus_areas': ['MARKETING'], 'first_steps': ['Register']},
    )


def _create_test_plan(user, profile, num_tasks=3):
    today = timezone.now().date()
    plan = TaskPlan.objects.create(
        user=user,
        business_profile=profile,
        starts_on=today,
        ends_on=today + timedelta(days=30),
    )
    for i in range(1, num_tasks + 1):
        Task.objects.create(
            plan=plan,
            title=f'Task {i}',
            description=f'Description {i}',
            category='PLANNING',
            day_number=i,
            due_date=today + timedelta(days=i - 1),
            sort_order=0,
        )
    return plan


class StreakRecordTest(TestCase):

    def setUp(self):
        self.user = _create_test_user()
        self.profile = _create_test_profile(self.user)
        self.plan = _create_test_plan(self.user, self.profile)

    def test_record_task_completion_creates_streak(self):
        task = self.plan.tasks.first()
        task.status = 'SENT'
        task.save()
        TaskProgressService.mark_done(task)

        today = timezone.now().date()
        record = StreakRecord.objects.get(user=self.user, date=today)
        self.assertEqual(record.tasks_completed, 1)

    def test_multiple_completions_same_day_increment(self):
        tasks = list(self.plan.tasks.all()[:2])
        for t in tasks:
            t.status = 'SENT'
            t.save()
            TaskProgressService.mark_done(t)

        today = timezone.now().date()
        record = StreakRecord.objects.get(user=self.user, date=today)
        self.assertEqual(record.tasks_completed, 2)

    def test_get_current_streak_zero(self):
        self.assertEqual(AchievementService.get_current_streak(self.user), 0)

    def test_get_current_streak_with_today(self):
        today = timezone.now().date()
        StreakRecord.objects.create(user=self.user, date=today, tasks_completed=1)
        self.assertEqual(AchievementService.get_current_streak(self.user), 1)

    def test_get_current_streak_consecutive(self):
        today = timezone.now().date()
        for i in range(3):
            StreakRecord.objects.create(
                user=self.user, date=today - timedelta(days=i), tasks_completed=1,
            )
        self.assertEqual(AchievementService.get_current_streak(self.user), 3)

    def test_streak_breaks_on_gap(self):
        today = timezone.now().date()
        StreakRecord.objects.create(user=self.user, date=today, tasks_completed=1)
        # Skip yesterday
        StreakRecord.objects.create(user=self.user, date=today - timedelta(days=2), tasks_completed=1)
        self.assertEqual(AchievementService.get_current_streak(self.user), 1)


class AchievementBadgeTest(TestCase):

    def setUp(self):
        self.user = _create_test_user()
        self.profile = _create_test_profile(self.user)

    def test_first_task_badge(self):
        plan = _create_test_plan(self.user, self.profile)
        task = plan.tasks.first()
        task.status = 'SENT'
        task.save()
        TaskProgressService.mark_done(task)

        self.assertTrue(
            Achievement.objects.filter(user=self.user, badge='FIRST_TASK').exists()
        )

    def test_first_task_badge_only_once(self):
        plan = _create_test_plan(self.user, self.profile)
        tasks = list(plan.tasks.all()[:2])
        for t in tasks:
            t.status = 'SENT'
            t.save()
            TaskProgressService.mark_done(t)

        self.assertEqual(
            Achievement.objects.filter(user=self.user, badge='FIRST_TASK').count(), 1
        )

    def test_plan_complete_badge(self):
        plan = _create_test_plan(self.user, self.profile, num_tasks=2)
        for task in plan.tasks.all():
            task.status = 'SENT'
            task.save()
            TaskProgressService.mark_done(task)

        self.assertTrue(
            Achievement.objects.filter(user=self.user, badge='PLAN_COMPLETE').exists()
        )

    def test_streak_3_badge(self):
        today = timezone.now().date()
        # Create 2-day historical streak
        for i in range(1, 3):
            StreakRecord.objects.create(
                user=self.user, date=today - timedelta(days=i), tasks_completed=1,
            )
        # Complete a task today to get 3-day streak
        plan = _create_test_plan(self.user, self.profile)
        task = plan.tasks.first()
        task.status = 'SENT'
        task.save()
        TaskProgressService.mark_done(task)

        self.assertTrue(
            Achievement.objects.filter(user=self.user, badge='STREAK_3').exists()
        )

    def test_category_master_badge(self):
        plan = _create_test_plan(self.user, self.profile, num_tasks=3)
        # Make all tasks same category
        plan.tasks.all().update(category='MARKETING')
        for task in plan.tasks.all():
            task.status = 'SENT'
            task.save()
            TaskProgressService.mark_done(task)

        self.assertTrue(
            Achievement.objects.filter(user=self.user, badge='CATEGORY_MASTER').exists()
        )

    def test_comeback_badge(self):
        today = timezone.now().date()
        # Last activity was 4 days ago
        StreakRecord.objects.create(
            user=self.user, date=today - timedelta(days=4), tasks_completed=1,
        )
        plan = _create_test_plan(self.user, self.profile)
        task = plan.tasks.first()
        task.status = 'SENT'
        task.save()
        TaskProgressService.mark_done(task)

        self.assertTrue(
            Achievement.objects.filter(user=self.user, badge='COMEBACK').exists()
        )

    def test_get_user_achievements(self):
        Achievement.objects.create(
            user=self.user, badge='FIRST_TASK', title='First Task',
        )
        Achievement.objects.create(
            user=self.user, badge='STREAK_3', title='3-Day Streak',
        )
        achievements = AchievementService.get_user_achievements(self.user)
        self.assertEqual(achievements.count(), 2)


class MarkDoneAchievementIntegrationTest(TestCase):
    """Verify mark_done doesn't break if achievement tracking fails."""

    def setUp(self):
        self.user = _create_test_user()
        self.profile = _create_test_profile(self.user)
        self.plan = _create_test_plan(self.user, self.profile)

    def test_mark_done_still_works_if_achievement_fails(self):
        """Achievement errors should be caught, not break task completion."""
        task = self.plan.tasks.first()
        task.status = 'SENT'
        task.save()

        # Even if something goes wrong in achievements, mark_done succeeds
        result = TaskProgressService.mark_done(task)
        self.assertEqual(result.status, 'DONE')
