from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from onboarding.models import BusinessProfile
from tasks.models import Task, TaskPlan
from tasks.services import TaskGenerationService, TaskProgressService


def _create_test_user():
    return User.objects.create_user('testuser', 'test@example.com', 'pass123')


def _create_test_profile(user):
    return BusinessProfile.objects.create(
        user=user,
        business_name='Test Bakery',
        business_type='Bakery',
        stage='IDEA',
        goals=['First 10 customers'],
        ai_assessment={
            'summary': 'Good idea',
            'focus_areas': ['MARKETING'],
            'first_steps': ['Register'],
        },
    )


def _create_test_plan(user, profile):
    today = timezone.now().date()
    plan = TaskPlan.objects.create(
        user=user,
        business_profile=profile,
        starts_on=today,
        ends_on=today + timedelta(days=30),
    )
    for i in range(1, 4):
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


class TaskGenerationServiceTest(TestCase):

    def setUp(self):
        self.user = _create_test_user()
        self.profile = _create_test_profile(self.user)

    @patch('tasks.services.call_claude_json')
    def test_generate_plan_creates_tasks(self, mock_claude):
        mock_claude.return_value = {
            'tasks': [
                {'day_number': 1, 'sort_order': 0, 'title': 'Register business',
                 'description': 'Go to city hall.', 'category': 'LEGAL',
                 'difficulty': 'MEDIUM', 'estimated_minutes': 60},
                {'day_number': 1, 'sort_order': 1, 'title': 'Set up email',
                 'description': 'Create Gmail.', 'category': 'DIGITAL',
                 'difficulty': 'EASY', 'estimated_minutes': 15},
            ],
        }
        plan = TaskGenerationService.generate_plan(self.profile)
        self.assertEqual(plan.tasks.count(), 2)
        self.assertEqual(plan.status, 'ACTIVE')

    @patch('tasks.services.call_claude_json')
    def test_generate_plan_fallback_on_error(self, mock_claude):
        from ai.claude_client import ClaudeClientError
        mock_claude.side_effect = ClaudeClientError('API down')
        plan = TaskGenerationService.generate_plan(self.profile)
        self.assertGreater(plan.tasks.count(), 0)

    def test_get_daily_tasks(self):
        plan = _create_test_plan(self.user, self.profile)
        today = timezone.now().date()
        tasks = TaskGenerationService.get_daily_tasks(self.user, today)
        self.assertEqual(tasks.count(), 1)

    def test_get_daily_tasks_no_plan(self):
        tasks = TaskGenerationService.get_daily_tasks(self.user)
        self.assertEqual(tasks.count(), 0)


class TaskProgressServiceTest(TestCase):

    def setUp(self):
        self.user = _create_test_user()
        self.profile = _create_test_profile(self.user)
        self.plan = _create_test_plan(self.user, self.profile)

    def _get_task(self, status='SENT'):
        task = self.plan.tasks.first()
        task.status = status
        task.save()
        return task

    def test_mark_done_from_sent(self):
        task = self._get_task('SENT')
        result = TaskProgressService.mark_done(task)
        self.assertEqual(result.status, 'DONE')
        self.assertIsNotNone(result.completed_at)

    def test_mark_done_from_pending(self):
        task = self._get_task('PENDING')
        result = TaskProgressService.mark_done(task)
        self.assertEqual(result.status, 'DONE')

    def test_mark_done_invalid_status(self):
        task = self._get_task('DONE')
        with self.assertRaises(ValueError):
            TaskProgressService.mark_done(task)

    def test_mark_skipped(self):
        task = self._get_task('SENT')
        result = TaskProgressService.mark_skipped(task)
        self.assertEqual(result.status, 'SKIPPED')
        self.assertIsNotNone(result.skipped_at)

    def test_mark_skipped_invalid_status(self):
        task = self._get_task('DONE')
        with self.assertRaises(ValueError):
            TaskProgressService.mark_skipped(task)

    def test_process_inbound_done(self):
        task = self._get_task('SENT')
        task.due_date = timezone.now().date()
        task.save()
        reply = TaskProgressService.process_inbound_reply(self.user, 'DONE')
        self.assertIn('done', reply.lower())
        task.refresh_from_db()
        self.assertEqual(task.status, 'DONE')

    def test_process_inbound_skip(self):
        task = self._get_task('SENT')
        task.due_date = timezone.now().date()
        task.save()
        reply = TaskProgressService.process_inbound_reply(self.user, 'SKIP')
        self.assertIn('skipped', reply.lower())
        task.refresh_from_db()
        self.assertEqual(task.status, 'SKIPPED')

    def test_process_inbound_help(self):
        reply = TaskProgressService.process_inbound_reply(self.user, 'HELP')
        self.assertIn('DONE', reply)
        self.assertIn('SKIP', reply)

    def test_process_inbound_unknown(self):
        reply = TaskProgressService.process_inbound_reply(self.user, 'blah blah')
        self.assertIn("didn't understand", reply.lower())

    def test_process_inbound_no_plan(self):
        self.plan.status = 'COMPLETED'
        self.plan.save()
        reply = TaskProgressService.process_inbound_reply(self.user, 'DONE')
        self.assertIn('active plan', reply.lower())

    def test_reschedule_task(self):
        task = self._get_task('PENDING')
        new_date = timezone.now().date() + timedelta(days=5)
        result = TaskProgressService.reschedule_task(task, new_date)
        self.assertEqual(result.status, 'RESCHEDULED')
        # Should have created a copy
        self.assertEqual(self.plan.tasks.count(), 4)
