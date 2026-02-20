"""OpenAI API client wrapper for the Business Building Assistant."""

import logging

from django.conf import settings

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)


class OpenAIClientError(Exception):
    """Raised when OpenAI API call fails."""
    pass


def call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    """Call OpenAI API and return the text response.

    Args:
        system_prompt: System message.
        user_prompt: User message content.
        model: Model to use. Defaults to OPENAI_MODEL_CHEAP from settings.
        max_tokens: Maximum tokens in response.

    Returns:
        Raw text response from OpenAI.

    Raises:
        OpenAIClientError: If the API call fails.
    """
    if not settings.OPENAI_API_KEY:
        raise OpenAIClientError('OPENAI_API_KEY not configured')

    model = model or settings.OPENAI_MODEL_CHEAP
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        text = response.choices[0].message.content
        logger.info(
            'OpenAI API call: model=%s, prompt_tokens=%d, completion_tokens=%d',
            model,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )
        return text
    except OpenAIError as e:
        logger.error('OpenAI API error: %s', e)
        raise OpenAIClientError(f'OpenAI API error: {e}') from e
