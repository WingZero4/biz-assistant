"""Management command: send daily tasks to users.

Runs every hour via PythonAnywhere scheduled task.
Finds users whose daily_send_hour matches the current hour
in their timezone. Idempotent — won't re-send if tasks already SENT today.
"""

import logging
from datetime import datetime

import zoneinfo

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from notifications.services import NotificationService
from tasks.services import TaskGenerationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send daily tasks to users based on their timezone and send hour'

    def handle(self, *args, **options):
        now_utc = timezone.now()
        sent_count = 0
        skip_count = 0

        # Get all onboarded users
        profiles = UserProfile.objects.filter(
            is_onboarded=True,
        ).select_related('user')

        for profile in profiles:
            try:
                # Check if it's the right hour in user's timezone
                user_tz = zoneinfo.ZoneInfo(profile.timezone)
                user_now = now_utc.astimezone(user_tz)

                if user_now.hour != profile.daily_send_hour:
                    continue

                user = profile.user
                today = user_now.date()

                # Get today's tasks
                tasks = list(
                    TaskGenerationService.get_daily_tasks(user, today)
                )

                if not tasks:
                    continue

                # Idempotent check — skip if any task already SENT today
                already_sent = any(t.status == 'SENT' for t in tasks)
                if already_sent:
                    skip_count += 1
                    continue

                # Personalize message
                pending_tasks = [t for t in tasks if t.status == 'PENDING']
                if not pending_tasks:
                    continue

                message = TaskGenerationService.personalize_daily_message(
                    pending_tasks, user,
                )

                # Send via preferred channels
                NotificationService.send_daily_tasks(user, pending_tasks, message)
                sent_count += 1

                self.stdout.write(
                    f'  Sent {len(pending_tasks)} tasks to {user.username}'
                )

            except Exception:
                logger.exception('Failed to send daily tasks for user %s', profile.user.username)

        self.stdout.write(self.style.SUCCESS(
            f'Daily tasks: {sent_count} sent, {skip_count} skipped (already sent)'
        ))
