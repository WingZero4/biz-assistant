"""OnboardingService — orchestrates the onboarding flow.

All onboarding mutations go through this service.
"""

import logging
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from ai.claude_client import ClaudeClientError, call_claude_json
from ai.prompts import (
    ONBOARDING_ASSESSMENT_SYSTEM,
    ONBOARDING_ASSESSMENT_USER,
)
from tasks.services import TaskGenerationService

from .models import BusinessProfile, Conversation

logger = logging.getLogger(__name__)


class OnboardingService:

    @staticmethod
    def create_business_profile(user: User, form_data: dict) -> BusinessProfile:
        """Create BusinessProfile from combined wizard form data."""
        # Parse goals from newline-separated text to list
        goals_text = form_data.get('goals', '')
        goals = [g.strip() for g in goals_text.split('\n') if g.strip()]

        profile = BusinessProfile.objects.create(
            user=user,
            business_name=form_data['business_name'],
            business_type=form_data['business_type'],
            stage=form_data['stage'],
            description=form_data.get('description', ''),
            goals=goals,
            target_audience=form_data.get('target_audience', ''),
            budget_range=form_data.get('budget_range', 'BOOTSTRAP'),
            location=form_data.get('location', ''),
        )
        return profile

    @staticmethod
    def run_ai_assessment(profile: BusinessProfile) -> dict:
        """Send profile to Claude for assessment. Updates profile fields."""
        user_prompt = ONBOARDING_ASSESSMENT_USER.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            stage=profile.get_stage_display(),
            description=profile.description or 'Not provided',
            goals=', '.join(profile.goals) if profile.goals else 'Not specified',
            target_audience=profile.target_audience or 'Not specified',
            budget_range=profile.get_budget_range_display(),
            location=profile.location or 'Not specified',
        )

        try:
            assessment = call_claude_json(
                ONBOARDING_ASSESSMENT_SYSTEM,
                user_prompt,
            )
        except ClaudeClientError:
            logger.exception('AI assessment failed for profile %d', profile.pk)
            assessment = OnboardingService._fallback_assessment(profile)

        profile.ai_assessment = assessment
        profile.ai_model_used = 'claude-sonnet'
        profile.assessment_generated_at = timezone.now()
        profile.save()

        # Store conversation for context
        Conversation.objects.create(
            user=profile.user,
            role='system',
            content=f'Assessment generated for {profile.business_name}',
            metadata={'assessment': assessment},
        )

        return assessment

    @staticmethod
    def generate_initial_plan(profile: BusinessProfile):
        """Generate the initial 30-day task plan."""
        return TaskGenerationService.generate_plan(profile)

    @staticmethod
    def complete_onboarding(user: User):
        """Mark user as onboarded."""
        user.profile.is_onboarded = True
        user.profile.save()

    @staticmethod
    def _fallback_assessment(profile: BusinessProfile) -> dict:
        """Generate a basic assessment when AI is unavailable."""
        return {
            'viability_score': 5,
            'key_strengths': ['Motivated founder', 'Clear business idea'],
            'key_risks': ['Market competition', 'Limited budget'],
            'focus_areas': ['PLANNING', 'DIGITAL', 'MARKETING'],
            'first_steps': [
                'Register your business name',
                'Set up a business email',
                'Create social media accounts',
                'Define your pricing',
                'Build a simple website or landing page',
            ],
            'time_to_revenue': '1-3 months',
            'plan_type': 'standard_30_day',
            'summary': (
                f'{profile.business_name} is in the {profile.get_stage_display()} stage. '
                'Focus on establishing your digital presence and building an initial customer base.'
            ),
        }
