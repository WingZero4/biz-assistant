"""Claude API client wrapper for the Business Building Assistant."""

import json
import logging

from django.conf import settings

import anthropic

logger = logging.getLogger(__name__)


class ClaudeClientError(Exception):
    """Raised when Claude API call fails."""
    pass


def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call Claude API and return the text response.

    Args:
        system_prompt: System message for Claude.
        user_prompt: User message content.
        max_tokens: Maximum tokens in response.

    Returns:
        Raw text response from Claude.

    Raises:
        ClaudeClientError: If the API call fails.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ClaudeClientError('ANTHROPIC_API_KEY not configured')

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_prompt}],
        )
        text = response.content[0].text
        logger.info(
            'Claude API call: model=%s, input_tokens=%d, output_tokens=%d',
            settings.ANTHROPIC_MODEL,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return text
    except anthropic.APIError as e:
        logger.error('Claude API error: %s', e)
        raise ClaudeClientError(f'Claude API error: {e}') from e


def call_claude_json(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> dict:
    """Call Claude API and parse the JSON response.

    Returns:
        Parsed JSON dict from Claude's response.

    Raises:
        ClaudeClientError: If the API call or JSON parsing fails.
    """
    text = call_claude(system_prompt, user_prompt, max_tokens)

    # Strip markdown fences if present
    cleaned = text.strip()
    if cleaned.startswith('```'):
        lines = cleaned.split('\n')
        # Remove first and last lines (``` markers)
        lines = [l for l in lines if not l.strip().startswith('```')]
        cleaned = '\n'.join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error('Claude JSON parse error: %s\nRaw response: %s', e, text[:500])
        raise ClaudeClientError(f'Failed to parse Claude JSON response: {e}') from e
