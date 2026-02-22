"""Document generation service."""

import logging

from django.conf import settings

from ai.claude_client import ClaudeClientError, call_claude
from ai.prompts import DOCUMENT_GENERATION_SYSTEM, DOCUMENT_GENERATION_USER

from .models import GeneratedDocument

logger = logging.getLogger(__name__)


class DocumentService:

    @staticmethod
    def generate_document(user, doc_type, topic, platform='', notes='') -> GeneratedDocument:
        """Generate a business document using Claude."""
        profile = getattr(user, 'business_profile', None)
        if not profile:
            raise ValueError('Business profile required to generate documents.')
        doc_type_label = dict(GeneratedDocument.DOC_TYPE_CHOICES).get(doc_type, doc_type)

        system_prompt = DOCUMENT_GENERATION_SYSTEM.format(
            business_name=profile.business_name,
            business_type=profile.business_type,
            stage=profile.get_stage_display(),
            description=profile.description or 'Not provided',
            target_audience=profile.target_audience or 'General audience',
            usp=profile.unique_selling_point or 'Not specified',
        )

        user_prompt = DOCUMENT_GENERATION_USER.format(
            doc_type=doc_type_label,
            platform=platform or 'General',
            topic=topic,
            notes=notes or 'None',
        )

        try:
            content = call_claude(system_prompt, user_prompt)
        except ClaudeClientError:
            logger.exception('Document generation failed')
            content = (
                f"Unable to generate {doc_type_label} right now. "
                "Please try again in a moment."
            )

        document = GeneratedDocument.objects.create(
            user=user,
            business_profile=profile,
            doc_type=doc_type,
            platform=platform,
            title=f'{doc_type_label}: {topic[:100]}',
            prompt_used=user_prompt,
            content=content,
            ai_model_used=settings.ANTHROPIC_MODEL,
        )

        return document

    @staticmethod
    def get_user_documents(user, doc_type=None):
        """Get user's generated documents, optionally filtered by type."""
        qs = GeneratedDocument.objects.filter(user=user)
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        return qs

    @staticmethod
    def toggle_favorite(document) -> GeneratedDocument:
        """Toggle favorite status of a document."""
        document.is_favorite = not document.is_favorite
        document.save(update_fields=['is_favorite'])
        return document
