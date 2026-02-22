"""Chat service — manages AI chat sessions."""

import logging
import uuid

from django.utils import timezone

from ai.claude_client import ClaudeClientError, call_claude_chat
from ai.prompts import CHAT_ADVISOR_SYSTEM
from tasks.models import TaskPlan

from .models import Conversation, WeeklyPulse

logger = logging.getLogger(__name__)


class ChatService:

    @staticmethod
    def get_or_create_session(user) -> str:
        """Get the latest active chat session or create a new one."""
        latest = Conversation.objects.filter(
            user=user, conversation_type='CHAT',
        ).order_by('-created_at').first()

        if latest and latest.session_id:
            return latest.session_id

        return ChatService.start_new_session(user)

    @staticmethod
    def start_new_session(user) -> str:
        """Create a new chat session and anchor it with a system message."""
        session_id = str(uuid.uuid4())
        Conversation.objects.create(
            user=user,
            role='system',
            content='New conversation started.',
            conversation_type='CHAT',
            session_id=session_id,
        )
        return session_id

    @staticmethod
    def get_chat_history(user, session_id, limit=50):
        """Get chat messages for a session."""
        return Conversation.objects.filter(
            user=user,
            conversation_type='CHAT',
            session_id=session_id,
        ).order_by('created_at')[:limit]

    @staticmethod
    def send_message(user, session_id, user_message) -> Conversation:
        """Save user message, call Claude, save and return response."""
        # Save user message
        Conversation.objects.create(
            user=user,
            role='user',
            content=user_message,
            conversation_type='CHAT',
            session_id=session_id,
        )

        # Build system prompt with context
        system_prompt = ChatService._build_system_prompt(user)

        # Build message history for Claude
        messages = ChatService._build_message_history(user, session_id)

        try:
            ai_response = call_claude_chat(system_prompt, messages)
        except ClaudeClientError:
            logger.exception('Chat API call failed')
            ai_response = (
                "I'm having trouble connecting right now. "
                "Please try again in a moment."
            )

        # Save assistant response
        response = Conversation.objects.create(
            user=user,
            role='assistant',
            content=ai_response,
            conversation_type='CHAT',
            session_id=session_id,
        )

        return response

    @staticmethod
    def _build_system_prompt(user) -> str:
        """Build a context-rich system prompt for the chat advisor."""
        profile = getattr(user, 'business_profile', None)
        if not profile:
            return CHAT_ADVISOR_SYSTEM.format(
                business_name='Unknown',
                business_type='Unknown',
                stage='Unknown',
                goals='Not set',
                description='No profile yet',
                assessment_summary='No assessment',
                plan_progress='No plan',
                recent_pulse='No data',
            )

        assessment = profile.ai_assessment or {}

        # Plan progress
        active_plan = TaskPlan.objects.filter(user=user, status='ACTIVE').first()
        if active_plan:
            total = active_plan.tasks.count()
            done = active_plan.tasks.filter(status='DONE').count()
            plan_progress = (
                f'{active_plan.title}: {done}/{total} tasks done '
                f'({active_plan.completion_pct}% complete), '
                f'Phase {active_plan.phase}'
            )
        else:
            plan_progress = 'No active plan'

        # Recent pulse
        pulse = WeeklyPulse.objects.filter(user=user).order_by('-week_of').first()
        if pulse:
            recent_pulse = (
                f'Week of {pulse.week_of}: '
                f'Rev=${pulse.revenue_this_week or 0}, '
                f'{pulse.new_customers} customers, '
                f'Energy: {pulse.get_energy_level_display()}, '
                f'Win: "{pulse.biggest_win}", '
                f'Blocker: "{pulse.biggest_blocker}"'
            )
        else:
            recent_pulse = 'No pulse data yet'

        return CHAT_ADVISOR_SYSTEM.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            stage=profile.get_stage_display(),
            goals=', '.join(profile.goals) if profile.goals else 'Not specified',
            description=profile.description or 'Not provided',
            assessment_summary=assessment.get('summary', 'No assessment available'),
            plan_progress=plan_progress,
            recent_pulse=recent_pulse,
        )

    @staticmethod
    def _build_message_history(user, session_id) -> list[dict]:
        """Convert chat history to Claude API format (last 20 messages)."""
        messages = Conversation.objects.filter(
            user=user,
            conversation_type='CHAT',
            session_id=session_id,
        ).order_by('-created_at')[:20]

        # Reverse to chronological order
        result = []
        for msg in reversed(messages):
            if msg.role in ('user', 'assistant'):
                result.append({'role': msg.role, 'content': msg.content})

        return result
