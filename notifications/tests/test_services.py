from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from notifications.models import MessageLog
from notifications.services import NotificationService
from onboarding.models import BusinessProfile
from tasks.models import Task, TaskPlan


class NotificationServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.user.profile.phone = '+15551234567'
        self.user.profile.save()

    def test_send_sms_no_phone(self):
        self.user.profile.phone = ''
        self.user.profile.save()
        result = NotificationService.send_sms(self.user, 'Hello')
        self.assertIsNone(result)

    @override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='', TWILIO_PHONE_NUMBER='')
    def test_send_sms_twilio_not_configured(self):
        log = NotificationService.send_sms(self.user, 'Hello')
        self.assertEqual(log.status, 'FAILED')
        self.assertIn('not configured', log.error_message)

    @override_settings(TWILIO_ACCOUNT_SID='test', TWILIO_AUTH_TOKEN='test', TWILIO_PHONE_NUMBER='+15550001111')
    @patch('notifications.services.NotificationService.send_sms')
    def test_send_sms_creates_log(self, mock_send):
        mock_log = MessageLog.objects.create(
            user=self.user, channel='SMS', direction='OUT',
            content='Hello', status='SENT',
        )
        mock_send.return_value = mock_log
        result = NotificationService.send_sms(self.user, 'Hello')
        self.assertEqual(result.channel, 'SMS')

    def test_send_email_no_email(self):
        self.user.email = ''
        self.user.save()
        result = NotificationService.send_email(self.user, 'Subject', '<p>Hi</p>', 'Hi')
        self.assertIsNone(result)

    @override_settings(SENDGRID_API_KEY='')
    def test_send_email_sendgrid_not_configured(self):
        log = NotificationService.send_email(self.user, 'Subject', '<p>Hi</p>', 'Hi')
        self.assertEqual(log.status, 'FAILED')
        self.assertIn('not configured', log.error_message)


class MessageLogTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')

    def test_str(self):
        log = MessageLog.objects.create(
            user=self.user, channel='SMS', direction='OUT',
            content='Hello', status='SENT',
        )
        self.assertIn('SMS', str(log))
        self.assertIn('OUT', str(log))
        self.assertIn('SENT', str(log))
