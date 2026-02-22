from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from onboarding.models import BusinessProfile
from tasks.models import Task, TaskPlan


class LandingViewTest(TestCase):

    def test_landing_page_renders(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Launch Your Business')

    def test_landing_redirects_authenticated_user(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dashboard/')


class SignupViewTest(TestCase):

    def test_signup_page_renders(self):
        response = self.client.get('/signup/')
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_redirects_to_onboarding(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertRedirects(response, '/onboarding/step/1/')


class DashboardViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')

    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_redirects_to_onboarding_if_not_onboarded(self):
        self.client.force_login(self.user)
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/onboarding/step/1/')

    def test_dashboard_renders_for_onboarded_user(self):
        self.user.profile.is_onboarded = True
        self.user.profile.save()
        self.client.force_login(self.user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)


class RescheduleViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.profile = BusinessProfile.objects.create(
            user=self.user, business_name='Test', business_type='Test',
            stage='IDEA', goals=['test'],
        )
        today = timezone.now().date()
        self.plan = TaskPlan.objects.create(
            user=self.user, business_profile=self.profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )
        self.task = Task.objects.create(
            plan=self.plan, title='Test task', description='Desc',
            category='PLANNING', day_number=1, due_date=today,
        )
        self.client.force_login(self.user)

    def test_reschedule_task(self):
        future = timezone.now().date() + timedelta(days=5)
        response = self.client.post(
            f'/tasks/{self.task.pk}/reschedule/',
            {'new_date': future.isoformat()},
        )
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'RESCHEDULED')

    def test_reschedule_past_date_rejected(self):
        past = timezone.now().date() - timedelta(days=1)
        response = self.client.post(
            f'/tasks/{self.task.pk}/reschedule/',
            {'new_date': past.isoformat()},
        )
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'PENDING')


class RegeneratePlanViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.user.profile.is_onboarded = True
        self.user.profile.save()
        self.profile = BusinessProfile.objects.create(
            user=self.user, business_name='Test', business_type='Test',
            stage='IDEA', goals=['test'],
            ai_assessment={'summary': 'Good', 'focus_areas': [], 'first_steps': []},
        )
        today = timezone.now().date()
        self.plan = TaskPlan.objects.create(
            user=self.user, business_profile=self.profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )

    @patch('tasks.services.call_claude_json')
    def test_regenerate_replaces_plan(self, mock_claude):
        from ai.claude_client import ClaudeClientError
        mock_claude.side_effect = ClaudeClientError('skip AI')
        self.client.force_login(self.user)
        response = self.client.post('/tasks/regenerate/')
        self.assertEqual(response.status_code, 302)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, 'REPLACED')
        self.assertTrue(
            TaskPlan.objects.filter(user=self.user, status='ACTIVE').exists()
        )


class PasswordChangeViewTest(TestCase):

    def test_password_change_requires_login(self):
        response = self.client.get('/password/change/')
        self.assertEqual(response.status_code, 302)

    def test_password_change_renders(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.client.force_login(user)
        response = self.client.get('/password/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Password')

    def test_password_reset_renders(self):
        response = self.client.get('/password/reset/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset Password')
