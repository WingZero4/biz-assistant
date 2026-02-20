"""NotificationService — SMS and email delivery.

All message sending goes through this service.
"""

import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import MessageLog

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def send_sms(user, body: str, related_task=None) -> MessageLog:
        """Send SMS via Twilio. Creates MessageLog."""
        phone = getattr(user, 'profile', None) and user.profile.phone
        if not phone:
            logger.warning('No phone number for user %s', user.username)
            return None

        log = MessageLog.objects.create(
            user=user,
            channel='SMS',
            direction='OUT',
            content=body,
            status='QUEUED',
            related_task=related_task,
        )

        if not settings.TWILIO_ACCOUNT_SID:
            logger.warning('Twilio not configured, SMS not sent')
            log.status = 'FAILED'
            log.error_message = 'Twilio not configured'
            log.save()
            return log

        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
            )
            log.twilio_sid = message.sid
            log.status = 'SENT'
            log.save()
            logger.info('SMS sent to %s, sid=%s', phone, message.sid)
        except Exception as e:
            logger.error('Twilio send failed: %s', e)
            log.status = 'FAILED'
            log.error_message = str(e)
            log.save()

        return log

    @staticmethod
    def send_email(
        user,
        subject: str,
        html_body: str,
        text_body: str,
        related_task=None,
    ) -> MessageLog:
        """Send email via SendGrid. Creates MessageLog."""
        email = user.email
        if not email:
            logger.warning('No email for user %s', user.username)
            return None

        log = MessageLog.objects.create(
            user=user,
            channel='EMAIL',
            direction='OUT',
            content=text_body,
            subject=subject,
            status='QUEUED',
            related_task=related_task,
        )

        if not settings.SENDGRID_API_KEY:
            logger.warning('SendGrid not configured, email not sent')
            log.status = 'FAILED'
            log.error_message = 'SendGrid not configured'
            log.save()
            return log

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=settings.SENDGRID_FROM_EMAIL,
                to_emails=email,
                subject=subject,
                html_content=html_body,
                plain_text_content=text_body,
            )
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)

            log.sendgrid_message_id = response.headers.get('X-Message-Id', '')
            log.status = 'SENT'
            log.save()
            logger.info('Email sent to %s, status=%d', email, response.status_code)
        except Exception as e:
            logger.error('SendGrid send failed: %s', e)
            log.status = 'FAILED'
            log.error_message = str(e)
            log.save()

        return log

    @staticmethod
    def send_daily_tasks(user, tasks, personalized_message: str) -> list:
        """Send daily tasks via user's preferred channel(s)."""
        logs = []
        channel = user.profile.preferred_channel

        # Build email content
        html_body = render_to_string('emails/daily_tasks.html', {
            'user': user,
            'tasks': tasks,
            'message': personalized_message,
        })
        text_body = personalized_message

        if channel in ('BOTH', 'SMS'):
            # SMS version — truncate to ~300 chars
            sms_body = personalized_message[:300]
            log = NotificationService.send_sms(user, sms_body, related_task=tasks[0] if tasks else None)
            if log:
                logs.append(log)

        if channel in ('BOTH', 'EMAIL'):
            subject = f"Day {tasks[0].day_number if tasks else '?'} — Your business tasks"
            log = NotificationService.send_email(
                user, subject, html_body, text_body,
                related_task=tasks[0] if tasks else None,
            )
            if log:
                logs.append(log)

        # Mark tasks as SENT
        for task in tasks:
            if task.status == 'PENDING':
                task.status = 'SENT'
                task.sent_at = timezone.now()
                task.personalized_message = personalized_message
                task.save()

        return logs

    @staticmethod
    def send_weekly_summary(user, html_body: str, text_body: str) -> list:
        """Send weekly progress summary via email."""
        logs = []
        subject = 'Your Weekly Business Progress Report'
        log = NotificationService.send_email(user, subject, html_body, text_body)
        if log:
            logs.append(log)
        return logs
