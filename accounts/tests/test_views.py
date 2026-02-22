from django.contrib.auth.models import User
from django.test import TestCase


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
