from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from onboarding.models import BusinessProfile
from tasks.models import Task, TaskPlan


class TaskPlanTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.profile = BusinessProfile.objects.create(
            user=self.user, business_name='Test', business_type='Test', stage='IDEA',
        )
        today = timezone.now().date()
        self.plan = TaskPlan.objects.create(
            user=self.user, business_profile=self.profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )

    def test_str(self):
        self.assertIn('testuser', str(self.plan))

    def test_completion_pct_no_tasks(self):
        self.assertEqual(self.plan.completion_pct, 0)

    def test_completion_pct_with_tasks(self):
        today = timezone.now().date()
        Task.objects.create(
            plan=self.plan, title='T1', description='D', category='PLANNING',
            day_number=1, due_date=today, status='DONE',
        )
        Task.objects.create(
            plan=self.plan, title='T2', description='D', category='PLANNING',
            day_number=2, due_date=today, status='PENDING',
        )
        self.assertEqual(self.plan.completion_pct, 50)


class TaskTest(TestCase):

    def setUp(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        profile = BusinessProfile.objects.create(
            user=user, business_name='Test', business_type='Test', stage='IDEA',
        )
        today = timezone.now().date()
        self.plan = TaskPlan.objects.create(
            user=user, business_profile=profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )

    def test_str(self):
        task = Task.objects.create(
            plan=self.plan, title='Do thing', description='D', category='PLANNING',
            day_number=1, due_date=timezone.now().date(),
        )
        self.assertIn('Do thing', str(task))
        self.assertIn('PENDING', str(task))

    def test_ordering(self):
        today = timezone.now().date()
        t2 = Task.objects.create(
            plan=self.plan, title='T2', description='D', category='PLANNING',
            day_number=1, due_date=today, sort_order=1,
        )
        t1 = Task.objects.create(
            plan=self.plan, title='T1', description='D', category='PLANNING',
            day_number=1, due_date=today, sort_order=0,
        )
        tasks = list(self.plan.tasks.all())
        self.assertEqual(tasks[0], t1)
        self.assertEqual(tasks[1], t2)
