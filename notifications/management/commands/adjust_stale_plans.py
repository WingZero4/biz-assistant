"""Management command: adjust plans for users with many skipped tasks.

Runs daily at 2am via PythonAnywhere scheduled task.
"""

import logging

from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from tasks.models import TaskPlan
from tasks.services import TaskGenerationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Adjust task plans for users with 3+ consecutive skipped tasks'

    def handle(self, *args, **options):
        adjusted_count = 0

        profiles = UserProfile.objects.filter(
            is_onboarded=True,
        ).select_related('user')

        for profile in profiles:
            try:
                user = profile.user
                plan = TaskPlan.objects.filter(
                    user=user, status='ACTIVE',
                ).first()

                if not plan:
                    continue

                # Check for 3+ consecutive skips
                recent_tasks = plan.tasks.filter(
                    status__in=['DONE', 'SKIPPED'],
                ).order_by('-due_date', '-sort_order')[:5]

                consecutive_skips = 0
                for task in recent_tasks:
                    if task.status == 'SKIPPED':
                        consecutive_skips += 1
                    else:
                        break

                if consecutive_skips >= 3:
                    TaskGenerationService.adjust_plan(
                        plan,
                        reason=f'{consecutive_skips} consecutive skipped tasks',
                    )
                    adjusted_count += 1
                    self.stdout.write(f'  Adjusted plan for {user.username}')

            except Exception:
                logger.exception(
                    'Failed to check/adjust plan for user %s',
                    profile.user.username,
                )

        self.stdout.write(self.style.SUCCESS(f'Plans adjusted: {adjusted_count}'))
