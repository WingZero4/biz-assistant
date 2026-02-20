from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from onboarding.models import BusinessProfile, Conversation
from onboarding.services import OnboardingService


class OnboardingServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.form_data = {
            'business_name': 'Test Bakery',
            'business_type': 'Bakery',
            'stage': 'IDEA',
            'description': 'A neighborhood bakery',
            'goals': 'First 10 customers\nLaunch website',
            'target_audience': 'Local families',
            'budget_range': 'LOW',
            'location': 'Austin, TX',
        }

    def test_create_business_profile(self):
        profile = OnboardingService.create_business_profile(self.user, self.form_data)
        self.assertIsInstance(profile, BusinessProfile)
        self.assertEqual(profile.business_name, 'Test Bakery')
        self.assertEqual(profile.goals, ['First 10 customers', 'Launch website'])
        self.assertEqual(profile.user, self.user)

    def test_create_profile_parses_goals(self):
        self.form_data['goals'] = 'Goal A\n\nGoal B\n  \nGoal C'
        profile = OnboardingService.create_business_profile(self.user, self.form_data)
        self.assertEqual(profile.goals, ['Goal A', 'Goal B', 'Goal C'])

    @patch('onboarding.services.call_claude_json')
    def test_run_ai_assessment_success(self, mock_claude):
        mock_claude.return_value = {
            'viability_score': 7,
            'key_strengths': ['Great location'],
            'key_risks': ['Competition'],
            'focus_areas': ['MARKETING'],
            'first_steps': ['Register business'],
            'time_to_revenue': '2-4 weeks',
            'plan_type': 'standard_30_day',
            'summary': 'Good potential.',
        }
        profile = OnboardingService.create_business_profile(self.user, self.form_data)
        assessment = OnboardingService.run_ai_assessment(profile)

        self.assertEqual(assessment['viability_score'], 7)
        profile.refresh_from_db()
        self.assertEqual(profile.ai_assessment['viability_score'], 7)
        self.assertIsNotNone(profile.assessment_generated_at)

    @patch('onboarding.services.call_claude_json')
    def test_run_ai_assessment_stores_conversation(self, mock_claude):
        mock_claude.return_value = {'viability_score': 5, 'summary': 'OK'}
        profile = OnboardingService.create_business_profile(self.user, self.form_data)
        OnboardingService.run_ai_assessment(profile)

        self.assertTrue(Conversation.objects.filter(user=self.user).exists())

    @patch('onboarding.services.call_claude_json')
    def test_run_ai_assessment_fallback_on_error(self, mock_claude):
        from ai.claude_client import ClaudeClientError
        mock_claude.side_effect = ClaudeClientError('API down')
        profile = OnboardingService.create_business_profile(self.user, self.form_data)
        assessment = OnboardingService.run_ai_assessment(profile)

        self.assertEqual(assessment['viability_score'], 5)
        self.assertIn('Motivated founder', assessment['key_strengths'])

    def test_complete_onboarding(self):
        OnboardingService.complete_onboarding(self.user)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_onboarded)
