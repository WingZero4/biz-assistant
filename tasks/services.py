"""Task services — all task mutations go through here."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ai.claude_client import ClaudeClientError, call_claude_json
from ai.openai_client import OpenAIClientError, call_openai
from ai.prompts import (
    DAILY_MESSAGE_SYSTEM,
    DAILY_MESSAGE_USER,
    PLAN_ADJUSTMENT_SYSTEM,
    PLAN_ADJUSTMENT_USER,
    PLAN_GENERATION_SYSTEM,
    PLAN_GENERATION_USER,
)
from onboarding.models import BusinessProfile

from .models import ResourceTemplate, Task, TaskPlan, TaskResource

logger = logging.getLogger(__name__)


class TaskGenerationService:

    @staticmethod
    @transaction.atomic
    def generate_plan(
        profile: BusinessProfile,
        duration_days: int = 30,
    ) -> TaskPlan:
        """Generate a full task plan using Claude. Creates TaskPlan + Tasks + Resources."""
        assessment = profile.ai_assessment or {}
        today = timezone.now().date()

        # Build display values for skills and platforms
        skill_map = dict(BusinessProfile.SKILL_CHOICES)
        skills_display = [skill_map.get(s, s) for s in (profile.owner_skills or [])]
        platform_map = dict(BusinessProfile.PLATFORM_CHOICES)
        platforms_display = [platform_map.get(p, p) for p in (profile.social_platforms or [])]

        system_prompt = PLAN_GENERATION_SYSTEM.format(duration_days=duration_days)
        user_prompt = PLAN_GENERATION_USER.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            stage=profile.get_stage_display(),
            description=profile.description or 'Not provided',
            goals=', '.join(profile.goals) if profile.goals else 'Not specified',
            budget_range=profile.get_budget_range_display(),
            location=profile.location or 'Not specified',
            niche=profile.niche or 'Not specified',
            business_model=profile.get_business_model_display(),
            unique_selling_point=profile.unique_selling_point or 'Not specified',
            known_competitors=', '.join(profile.known_competitors) if profile.known_competitors else 'None listed',
            owner_skills=', '.join(skills_display) if skills_display else 'None listed',
            business_experience=profile.get_business_experience_display(),
            hours_per_day=profile.hours_per_day,
            has_website='Yes' if profile.has_website else 'No',
            has_domain='Yes' if profile.has_domain else 'No',
            has_branding='Yes' if profile.has_branding else 'No',
            social_platforms=', '.join(platforms_display) if platforms_display else 'None',
            has_email_list='Yes' if profile.has_email_list else 'No',
            assessment_summary=assessment.get('summary', 'No assessment available'),
            focus_areas=', '.join(assessment.get('focus_areas', [])),
            first_steps=', '.join(assessment.get('first_steps', [])),
            duration_days=duration_days,
        )

        try:
            result = call_claude_json(system_prompt, user_prompt, max_tokens=16384)
            tasks_data = result.get('tasks', [])
        except ClaudeClientError:
            logger.exception('Plan generation failed, using fallback')
            tasks_data = TaskGenerationService._fallback_tasks(profile, duration_days)

        plan = TaskPlan.objects.create(
            user=profile.user,
            business_profile=profile,
            title=f'{duration_days}-Day Launch Plan',
            starts_on=today,
            ends_on=today + timedelta(days=duration_days),
            ai_generation_metadata={
                'model': settings.ANTHROPIC_MODEL,
                'task_count': len(tasks_data),
                'generated_at': timezone.now().isoformat(),
            },
        )

        for task_data in tasks_data:
            day_num = task_data.get('day_number', 1)
            task = Task.objects.create(
                plan=plan,
                title=task_data.get('title', 'Untitled task'),
                description=task_data.get('description', ''),
                category=task_data.get('category', 'PLANNING'),
                difficulty=task_data.get('difficulty', 'MEDIUM'),
                estimated_minutes=task_data.get('estimated_minutes', 30),
                day_number=day_num,
                due_date=today + timedelta(days=day_num - 1),
                sort_order=task_data.get('sort_order', 0),
            )

            # Create resources for this task
            resources_data = task_data.get('resources', [])
            TaskGenerationService._create_task_resources(
                task, resources_data, profile,
            )

        logger.info(
            'Generated plan %d with %d tasks for user %s',
            plan.pk, len(tasks_data), profile.user.username,
        )
        return plan

    @staticmethod
    def _find_library_match(resource_type, title, category, business_type):
        """Search the resource library for a matching reviewed template."""
        # Prefer REVIEWED templates that match business type + category
        matches = ResourceTemplate.objects.filter(
            status='REVIEWED',
            resource_type=resource_type,
        )
        # Try business_type + category match first
        for tmpl in matches:
            biz_types = tmpl.business_types or []
            cats = tmpl.categories or []
            if business_type.lower() in [b.lower() for b in biz_types] and category in cats:
                return tmpl
        # Fallback: category match only
        for tmpl in matches:
            cats = tmpl.categories or []
            if category in cats:
                return tmpl
        return None

    @staticmethod
    def _create_task_resources(task, resources_data, profile):
        """Create TaskResource records from AI-generated resource data.

        For each resource:
        1. Check library for an existing reviewed template
        2. If found, clone it (increment times_used)
        3. If not found, save AI output as new DRAFT ResourceTemplate + TaskResource
        """
        for idx, res in enumerate(resources_data):
            res_type = res.get('type', 'GUIDE')
            title = res.get('title', 'Resource')
            content = res.get('content', '')
            url = res.get('url', '')

            # Check library for existing reviewed template
            library_match = TaskGenerationService._find_library_match(
                res_type, title, task.category, profile.business_type,
            )

            if library_match:
                # Reuse reviewed template
                library_match.times_used += 1
                library_match.save(update_fields=['times_used'])
                TaskResource.objects.create(
                    task=task,
                    template=library_match,
                    title=library_match.title,
                    resource_type=library_match.resource_type,
                    content=library_match.content,
                    external_url=library_match.external_url,
                    sort_order=idx,
                )
            else:
                # Save as new DRAFT in the library
                template = ResourceTemplate.objects.create(
                    title=title,
                    resource_type=res_type,
                    content=content,
                    external_url=url,
                    business_types=[profile.business_type],
                    categories=[task.category],
                    tags=[],
                    status='DRAFT',
                    times_used=1,
                    ai_model_used=settings.ANTHROPIC_MODEL,
                )
                TaskResource.objects.create(
                    task=task,
                    template=template,
                    title=title,
                    resource_type=res_type,
                    content=content,
                    external_url=url,
                    sort_order=idx,
                )

    @staticmethod
    def get_daily_tasks(user, date=None):
        """Get tasks scheduled for a given date."""
        if date is None:
            date = timezone.now().date()

        active_plan = TaskPlan.objects.filter(
            user=user, status='ACTIVE',
        ).first()
        if not active_plan:
            return Task.objects.none()

        return active_plan.tasks.filter(due_date=date)

    @staticmethod
    def personalize_daily_message(
        tasks,
        user,
        channel: str = 'SMS',
    ) -> str:
        """Use OpenAI to create a personalized daily message."""
        profile = getattr(user, 'business_profile', None)
        if not profile:
            return TaskGenerationService._simple_task_message(tasks)

        active_plan = TaskPlan.objects.filter(
            user=user, status='ACTIVE',
        ).first()

        task_list = '\n'.join(
            f'- {t.title} (~{t.estimated_minutes} min)'
            for t in tasks
        )

        # Check yesterday's status
        yesterday = timezone.now().date() - timedelta(days=1)
        yesterday_tasks = Task.objects.filter(
            plan=active_plan, due_date=yesterday,
        ) if active_plan else Task.objects.none()
        done_count = yesterday_tasks.filter(status='DONE').count()
        total_yesterday = yesterday_tasks.count()
        if total_yesterday > 0:
            yesterday_status = f'{done_count}/{total_yesterday} completed'
        else:
            yesterday_status = 'No tasks yesterday'

        user_prompt = DAILY_MESSAGE_USER.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            day_number=tasks[0].day_number if tasks else 1,
            total_days=active_plan.duration_days if active_plan else 30,
            completion_pct=active_plan.completion_pct if active_plan else 0,
            yesterday_status=yesterday_status,
            task_list=task_list,
            channel=channel,
        )

        try:
            return call_openai(DAILY_MESSAGE_SYSTEM, user_prompt)
        except OpenAIClientError:
            logger.exception('Daily message personalization failed')
            return TaskGenerationService._simple_task_message(tasks)

    @staticmethod
    def adjust_plan(task_plan: TaskPlan, reason: str = 'Multiple skips'):
        """Use Claude to adjust remaining tasks based on progress."""
        profile = task_plan.business_profile

        completed = list(task_plan.tasks.filter(status='DONE').values_list('title', flat=True))
        skipped = list(task_plan.tasks.filter(status='SKIPPED').values_list('title', flat=True))
        remaining = list(
            task_plan.tasks.filter(status='PENDING')
            .values('id', 'title', 'day_number', 'category')
        )

        user_prompt = PLAN_ADJUSTMENT_USER.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            completed_tasks=', '.join(completed) or 'None',
            skipped_tasks=', '.join(skipped) or 'None',
            remaining_tasks=str(remaining),
            reason=reason,
        )

        try:
            result = call_claude_json(PLAN_ADJUSTMENT_SYSTEM, user_prompt)
        except ClaudeClientError:
            logger.exception('Plan adjustment failed')
            return

        # Process removals
        remove_ids = result.get('remove_task_ids', [])
        if remove_ids:
            task_plan.tasks.filter(id__in=remove_ids, status='PENDING').delete()

        # Process reschedules
        today = timezone.now().date()
        for item in result.get('reschedule', []):
            task = task_plan.tasks.filter(id=item.get('task_id'), status='PENDING').first()
            if task:
                new_day = item.get('new_day_number', task.day_number)
                task.day_number = new_day
                task.due_date = task_plan.starts_on + timedelta(days=new_day - 1)
                task.status = 'RESCHEDULED'
                task.rescheduled_to = task.due_date
                task.save()

        # Add new tasks
        for new_task in result.get('new_tasks', []):
            day_num = new_task.get('day_number', 1)
            Task.objects.create(
                plan=task_plan,
                title=new_task.get('title', 'New task'),
                description=new_task.get('description', ''),
                category=new_task.get('category', 'PLANNING'),
                difficulty=new_task.get('difficulty', 'MEDIUM'),
                estimated_minutes=new_task.get('estimated_minutes', 30),
                day_number=day_num,
                due_date=task_plan.starts_on + timedelta(days=day_num - 1),
                sort_order=new_task.get('sort_order', 0),
            )

        logger.info('Adjusted plan %d: %s', task_plan.pk, result.get('reasoning', ''))

    @staticmethod
    def _fallback_tasks(profile, duration_days):
        """Generate basic tasks when AI is unavailable."""
        return [
            {'day_number': 1, 'sort_order': 0, 'title': 'Define your business mission statement',
             'description': 'Write a clear, one-sentence mission statement for your business.',
             'category': 'PLANNING', 'difficulty': 'EASY', 'estimated_minutes': 20},
            {'day_number': 1, 'sort_order': 1, 'title': 'Research your competitors',
             'description': 'Find 3-5 competitors and note their strengths and weaknesses.',
             'category': 'PLANNING', 'difficulty': 'MEDIUM', 'estimated_minutes': 45},
            {'day_number': 2, 'sort_order': 0, 'title': 'Choose your business name',
             'description': 'Brainstorm 5 names, check domain availability, pick the best one.',
             'category': 'OPERATIONS', 'difficulty': 'MEDIUM', 'estimated_minutes': 30},
            {'day_number': 2, 'sort_order': 1, 'title': 'Set up a business email',
             'description': 'Create a professional email address for your business.',
             'category': 'DIGITAL', 'difficulty': 'EASY', 'estimated_minutes': 15},
            {'day_number': 3, 'sort_order': 0, 'title': 'Create social media accounts',
             'description': 'Set up Instagram and Facebook pages for your business.',
             'category': 'DIGITAL', 'difficulty': 'EASY', 'estimated_minutes': 30},
            {'day_number': 3, 'sort_order': 1, 'title': 'Define your pricing',
             'description': 'Research market rates and set initial pricing for your top 3 products/services.',
             'category': 'FINANCE', 'difficulty': 'MEDIUM', 'estimated_minutes': 45},
        ]

    @staticmethod
    def _simple_task_message(tasks):
        """Simple message when AI is unavailable."""
        lines = ["Here are today's tasks:"]
        for i, task in enumerate(tasks, 1):
            lines.append(f'{i}. {task.title} (~{task.estimated_minutes} min)')
        lines.append('Reply DONE or SKIP when finished!')
        return '\n'.join(lines)


class TaskProgressService:

    @staticmethod
    def mark_done(task: Task, user_response: str = '') -> Task:
        """Mark task as completed."""
        if task.status not in ('PENDING', 'SENT'):
            raise ValueError(
                f'Cannot mark task as done from status {task.status}'
            )
        task.status = 'DONE'
        task.completed_at = timezone.now()
        task.user_response = user_response
        task.save()
        return task

    @staticmethod
    def mark_skipped(task: Task, user_response: str = '') -> Task:
        """Mark task as skipped. Triggers plan adjustment if 3+ skips."""
        if task.status not in ('PENDING', 'SENT'):
            raise ValueError(
                f'Cannot skip task from status {task.status}'
            )
        task.status = 'SKIPPED'
        task.skipped_at = timezone.now()
        task.user_response = user_response
        task.save()

        # Check for consecutive skips
        recent_skips = task.plan.tasks.filter(
            status='SKIPPED',
        ).order_by('-skipped_at')[:3]
        if recent_skips.count() >= 3:
            TaskGenerationService.adjust_plan(
                task.plan, reason='3+ consecutive skipped tasks',
            )

        return task

    @staticmethod
    def reschedule_task(task: Task, new_date) -> Task:
        """Reschedule task to a future date."""
        if task.status not in ('PENDING', 'SENT'):
            raise ValueError(
                f'Cannot reschedule task from status {task.status}'
            )
        task.status = 'RESCHEDULED'
        task.rescheduled_to = new_date
        task.save()

        # Create a copy for the new date
        Task.objects.create(
            plan=task.plan,
            title=task.title,
            description=task.description,
            category=task.category,
            difficulty=task.difficulty,
            estimated_minutes=task.estimated_minutes,
            day_number=task.day_number,
            due_date=new_date,
            sort_order=task.sort_order,
        )
        return task

    @staticmethod
    def process_inbound_reply(user, message_text: str) -> str:
        """Parse SMS reply and update task status.

        Supported replies: DONE, SKIP, DONE 2, SKIP 1, HELP
        Returns acknowledgment message.
        """
        text = message_text.strip().upper()
        today = timezone.now().date()

        # Get today's sent/pending tasks
        active_plan = TaskPlan.objects.filter(
            user=user, status='ACTIVE',
        ).first()
        if not active_plan:
            return "You don't have an active plan. Visit our website to get started!"

        today_tasks = list(
            active_plan.tasks.filter(
                due_date=today, status__in=['SENT', 'PENDING'],
            ).order_by('sort_order')
        )

        if not today_tasks:
            return "No pending tasks for today. Great job!"

        # Parse command
        if text.startswith('DONE'):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                idx = int(parts[1]) - 1
                if 0 <= idx < len(today_tasks):
                    task = today_tasks[idx]
                else:
                    return f"Invalid task number. You have {len(today_tasks)} tasks today."
            else:
                task = today_tasks[0]

            TaskProgressService.mark_done(task, user_response=message_text)
            remaining = len(today_tasks) - 1
            if remaining > 0:
                return f"'{task.title}' done! {remaining} task(s) remaining today."
            return f"'{task.title}' done! All tasks complete for today!"

        elif text.startswith('SKIP'):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                idx = int(parts[1]) - 1
                if 0 <= idx < len(today_tasks):
                    task = today_tasks[idx]
                else:
                    return f"Invalid task number. You have {len(today_tasks)} tasks today."
            else:
                task = today_tasks[0]

            TaskProgressService.mark_skipped(task, user_response=message_text)
            return f"'{task.title}' skipped. We'll adjust your plan accordingly."

        elif text == 'HELP':
            return (
                "Reply DONE to complete your current task, "
                "SKIP to skip it, or DONE 2 / SKIP 2 for a specific task number."
            )

        else:
            return (
                "I didn't understand that. "
                "Reply DONE, SKIP, or HELP."
            )
