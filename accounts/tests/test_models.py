from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import UserProfile


class UserProfileTest(TestCase):

    def test_profile_created_on_user_create(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)

    def test_profile_defaults(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        profile = user.profile
        self.assertEqual(profile.timezone, 'America/New_York')
        self.assertEqual(profile.preferred_channel, 'BOTH')
        self.assertEqual(profile.daily_send_hour, 8)
        self.assertFalse(profile.is_onboarded)
        self.assertEqual(profile.phone, '')

    def test_str(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.assertEqual(str(user.profile), 'testuser profile')
