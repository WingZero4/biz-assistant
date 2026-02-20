"""Management command: send weekly progress summaries.

Runs Sunday morning via PythonAnywhere scheduled task.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from ai.openai_client import OpenAIClientError, call_openai
from ai.prompts import WEEKLY_SUMMARY_SYSTEM, WEEKLY_SUMMARY_USER
from accounts.models import UserProfile
from notifications.services import NotificationService
from tasks.models import TaskPlan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send weekly progress summary emails to all active users'

    def handle(self, *args, **options):
        sent_count = 0
        today = timezone.now().date()
        week_start = today - timedelta(days=7)

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

                # Calculate stats
                week_tasks = plan.tasks.filter(
                    due_date__gte=week_start, due_date__lt=today,
                )
                completed = week_tasks.filter(status='DONE')
                skipped = week_tasks.filter(status='SKIPPED')
                completed_count = completed.count()
                skipped_count = skipped.count()
                total_week = week_tasks.count()
                completion_rate = round(
                    (completed_count / total_week * 100) if total_week > 0 else 0
                )

                # Next week preview
                next_week_tasks = plan.tasks.filter(
                    due_date__gte=today,
                    due_date__lt=today + timedelta(days=7),
                    status='PENDING',
                )
                next_week_titles = list(
                    next_week_tasks.values_list('title', flat=True)[:5]
                )

                # Calculate week number
                days_in = (today - plan.starts_on).days
                week_number = (days_in // 7) + 1
                total_weeks = (plan.duration_days // 7) or 4

                # Generate AI summary
                try:
                    summary_html = call_openai(
                        WEEKLY_SUMMARY_SYSTEM,
                        WEEKLY_SUMMARY_USER.format(
                            business_name=plan.business_profile.business_name,
                            business_type=plan.business_profile.business_type,
                            week_number=week_number,
                            total_weeks=total_weeks,
                            completed_count=completed_count,
                            skipped_count=skipped_count,
                            completion_rate=completion_rate,
                            completed_list=', '.join(
                                completed.values_list('title', flat=True)
                            ) or 'None',
                            skipped_list=', '.join(
                                skipped.values_list('title', flat=True)
                            ) or 'None',
                            next_week_preview=', '.join(next_week_titles) or 'Plan complete!',
                            overall_pct=plan.completion_pct,
                        ),
                        model=settings.OPENAI_MODEL_MID,
                    )
                except OpenAIClientError:
                    summary_html = f'<p>This week you completed {completed_count} tasks. Keep going!</p>'

                # Render email template
                html_body = render_to_string('emails/weekly_summary.html', {
                    'summary_html': summary_html,
                    'completed_count': completed_count,
                    'skipped_count': skipped_count,
                    'completion_rate': completion_rate,
                    'overall_pct': plan.completion_pct,
                })

                text_body = f'Week {week_number}: {completed_count} tasks completed, {completion_rate}% rate.'

                NotificationService.send_weekly_summary(user, html_body, text_body)
                sent_count += 1
                self.stdout.write(f'  Weekly summary sent to {user.username}')

            except Exception:
                logger.exception('Failed to send weekly summary for user %s', profile.user.username)

        self.stdout.write(self.style.SUCCESS(f'Weekly summaries sent: {sent_count}'))
