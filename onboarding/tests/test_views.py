from django.contrib.auth.models import User
from django.test import TestCase


class OnboardingWizardTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.client.force_login(self.user)

    def test_step_1_renders(self):
        response = self.client.get('/onboarding/step/1/')
        self.assertEqual(response.status_code, 200)

    def test_step_1_stores_data_in_session(self):
        response = self.client.post('/onboarding/step/1/', {
            'business_name': 'Test Shop',
            'business_type': 'Retail',
            'stage': 'IDEA',
        })
        self.assertRedirects(response, '/onboarding/step/2/')
        session = self.client.session
        self.assertEqual(session['onboarding_data']['business_name'], 'Test Shop')

    def test_step_2_requires_step_1(self):
        response = self.client.get('/onboarding/step/2/')
        self.assertRedirects(response, '/onboarding/step/1/')

    def test_step_2_works_after_step_1(self):
        self.client.post('/onboarding/step/1/', {
            'business_name': 'Test Shop',
            'business_type': 'Retail',
            'stage': 'IDEA',
        })
        response = self.client.get('/onboarding/step/2/')
        self.assertEqual(response.status_code, 200)

    def test_step_3_requires_step_1(self):
        response = self.client.get('/onboarding/step/3/')
        self.assertRedirects(response, '/onboarding/step/1/')

    def test_step_3_renders_after_step_1(self):
        self._complete_step_1()
        response = self.client.get('/onboarding/step/3/')
        self.assertEqual(response.status_code, 200)

    def test_step_3_stores_skills(self):
        self._complete_step_1()
        response = self.client.post('/onboarding/step/3/', {
            'owner_skills': ['social_media', 'design'],
            'business_experience': 'SOME',
            'hours_per_day': 4,
        })
        self.assertRedirects(response, '/onboarding/step/4/')
        session = self.client.session
        self.assertEqual(session['onboarding_data']['business_experience'], 'SOME')

    def test_step_4_requires_step_1(self):
        response = self.client.get('/onboarding/step/4/')
        self.assertRedirects(response, '/onboarding/step/1/')

    def test_step_4_renders_after_step_1(self):
        self._complete_step_1()
        response = self.client.get('/onboarding/step/4/')
        self.assertEqual(response.status_code, 200)

    def test_step_5_requires_step_1(self):
        response = self.client.get('/onboarding/step/5/')
        self.assertRedirects(response, '/onboarding/step/1/')

    def test_step_5_renders_after_step_1(self):
        self._complete_step_1()
        response = self.client.get('/onboarding/step/5/')
        self.assertEqual(response.status_code, 200)

    def test_step_6_requires_step_1(self):
        response = self.client.get('/onboarding/step/6/')
        self.assertRedirects(response, '/onboarding/step/1/')

    def test_step_6_renders_after_step_1(self):
        self._complete_step_1()
        response = self.client.get('/onboarding/step/6/')
        self.assertEqual(response.status_code, 200)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get('/onboarding/step/1/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def _complete_step_1(self):
        self.client.post('/onboarding/step/1/', {
            'business_name': 'Test Shop',
            'business_type': 'Retail',
            'stage': 'IDEA',
        })
