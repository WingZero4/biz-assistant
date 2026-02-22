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

        # Parse competitors from newline-separated text
        competitors_text = form_data.get('known_competitors', '')
        competitors = [c.strip() for c in competitors_text.split('\n') if c.strip()]

        defaults = {
            'business_name': form_data['business_name'],
            'business_type': form_data['business_type'],
            'stage': form_data['stage'],
            'description': form_data.get('description', ''),
            'goals': goals,
            'target_audience': form_data.get('target_audience', ''),
            'budget_range': form_data.get('budget_range', 'BOOTSTRAP'),
            'location': form_data.get('location', ''),
            # Skills & Experience
            'owner_skills': form_data.get('owner_skills', []),
            'business_experience': form_data.get('business_experience', 'NONE'),
            'hours_per_day': int(form_data.get('hours_per_day', 2)),
            'education_background': form_data.get('education_background', ''),
            # Industry Details
            'niche': form_data.get('niche', ''),
            'known_competitors': competitors,
            'unique_selling_point': form_data.get('unique_selling_point', ''),
            'business_model': form_data.get('business_model', 'PRODUCT'),
            # Stage-specific context
            'current_revenue': form_data.get('current_revenue', ''),
            'team_size': form_data.get('team_size', ''),
            'biggest_challenges': form_data.get('biggest_challenges', ''),
            # Digital Presence
            'has_website': form_data.get('has_website', False),
            'has_social_media': form_data.get('has_social_media', False),
            'social_platforms': form_data.get('social_platforms', []),
            'has_email_list': form_data.get('has_email_list', False),
            'has_domain': form_data.get('has_domain', False),
            'has_branding': form_data.get('has_branding', False),
        }
        profile, _created = BusinessProfile.objects.update_or_create(
            user=user, defaults=defaults,
        )
        return profile

    @staticmethod
    def run_ai_assessment(profile: BusinessProfile) -> dict:
        """Send profile to Claude for assessment. Updates profile fields."""
        skill_map = dict(BusinessProfile.SKILL_CHOICES)
        skills_display = [skill_map.get(s, s) for s in (profile.owner_skills or [])]
        platform_map = dict(BusinessProfile.PLATFORM_CHOICES)
        platforms_display = [platform_map.get(p, p) for p in (profile.social_platforms or [])]

        user_prompt = ONBOARDING_ASSESSMENT_USER.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            stage=profile.get_stage_display(),
            description=profile.description or 'Not provided',
            goals=', '.join(profile.goals) if profile.goals else 'Not specified',
            target_audience=profile.target_audience or 'Not specified',
            budget_range=profile.get_budget_range_display(),
            location=profile.location or 'Not specified',
            niche=profile.niche or 'Not specified',
            business_model=profile.get_business_model_display(),
            unique_selling_point=profile.unique_selling_point or 'Not specified',
            known_competitors=', '.join(profile.known_competitors) if profile.known_competitors else 'None listed',
            owner_skills=', '.join(skills_display) if skills_display else 'None listed',
            business_experience=profile.get_business_experience_display(),
            hours_per_day=profile.hours_per_day,
            current_revenue=profile.current_revenue or 'Not specified',
            team_size=profile.team_size or 'Not specified',
            biggest_challenges=profile.biggest_challenges or 'None listed',
            has_website='Yes' if profile.has_website else 'No',
            has_domain='Yes' if profile.has_domain else 'No',
            has_branding='Yes' if profile.has_branding else 'No',
            social_platforms=', '.join(platforms_display) if platforms_display else 'None',
            has_email_list='Yes' if profile.has_email_list else 'No',
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
