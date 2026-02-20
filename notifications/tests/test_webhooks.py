import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from accounts.models import UserProfile
from notifications.models import MessageLog
from onboarding.models import BusinessProfile
from tasks.models import Task, TaskPlan

from datetime import timedelta
from django.utils import timezone


def _setup_user_with_plan():
    """Create a user with a profile, business profile, plan, and today's task."""
    user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
    user.profile.phone = '+15551234567'
    user.profile.is_onboarded = True
    user.profile.save()

    profile = BusinessProfile.objects.create(
        user=user, business_name='Test Biz', business_type='Test', stage='IDEA',
    )
    today = timezone.now().date()
    plan = TaskPlan.objects.create(
        user=user, business_profile=profile,
        starts_on=today, ends_on=today + timedelta(days=30),
    )
    task = Task.objects.create(
        plan=plan, title='Test Task', description='Do it', category='PLANNING',
        day_number=1, due_date=today, status='SENT',
    )
    return user, plan, task


@override_settings(TWILIO_AUTH_TOKEN='')
class TwilioInboundWebhookTest(TestCase):

    def setUp(self):
        self.user, self.plan, self.task = _setup_user_with_plan()

    def test_inbound_done(self):
        response = self.client.post('/webhooks/twilio/inbound/', {
            'From': '+15551234567',
            'Body': 'DONE',
            'MessageSid': 'SM123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/xml', response['Content-Type'])
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'DONE')

    def test_inbound_skip(self):
        response = self.client.post('/webhooks/twilio/inbound/', {
            'From': '+15551234567',
            'Body': 'SKIP',
            'MessageSid': 'SM124',
        })
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'SKIPPED')

    def test_inbound_help(self):
        response = self.client.post('/webhooks/twilio/inbound/', {
            'From': '+15551234567',
            'Body': 'HELP',
            'MessageSid': 'SM125',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'DONE', response.content)

    def test_inbound_unknown_number(self):
        response = self.client.post('/webhooks/twilio/inbound/', {
            'From': '+19999999999',
            'Body': 'DONE',
            'MessageSid': 'SM126',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.content)

    def test_inbound_creates_message_log(self):
        self.client.post('/webhooks/twilio/inbound/', {
            'From': '+15551234567',
            'Body': 'DONE',
            'MessageSid': 'SM127',
        })
        # Should have inbound + outbound reply logs
        logs = MessageLog.objects.filter(user=self.user)
        self.assertEqual(logs.count(), 2)
        self.assertTrue(logs.filter(direction='IN').exists())
        self.assertTrue(logs.filter(direction='OUT').exists())


@override_settings(TWILIO_AUTH_TOKEN='')
class TwilioStatusCallbackTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.log = MessageLog.objects.create(
            user=self.user, channel='SMS', direction='OUT',
            content='Hello', status='SENT', twilio_sid='SM999',
        )

    def test_delivered_status(self):
        response = self.client.post('/webhooks/twilio/status/', {
            'MessageSid': 'SM999',
            'MessageStatus': 'delivered',
        })
        self.assertEqual(response.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'DELIVERED')

    def test_failed_status(self):
        self.client.post('/webhooks/twilio/status/', {
            'MessageSid': 'SM999',
            'MessageStatus': 'failed',
        })
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'FAILED')


class SendGridEventWebhookTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.log = MessageLog.objects.create(
            user=self.user, channel='EMAIL', direction='OUT',
            content='Hi', status='SENT', sendgrid_message_id='abc123',
        )

    def test_delivered_event(self):
        events = [{'event': 'delivered', 'sg_message_id': 'abc123.filter'}]
        response = self.client.post(
            '/webhooks/sendgrid/events/',
            data=json.dumps(events),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'DELIVERED')

    def test_bounce_event(self):
        events = [{'event': 'bounce', 'sg_message_id': 'abc123.filter'}]
        self.client.post(
            '/webhooks/sendgrid/events/',
            data=json.dumps(events),
            content_type='application/json',
        )
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, 'FAILED')
