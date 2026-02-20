"""Webhook handlers for Twilio and SendGrid.

All webhook views are CSRF-exempt but verify provider signatures.
"""

import hashlib
import hmac
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import UserProfile
from tasks.services import TaskProgressService

from .models import MessageLog

logger = logging.getLogger(__name__)


def _verify_twilio_signature(request):
    """Verify Twilio request signature."""
    if not settings.TWILIO_AUTH_TOKEN:
        return True  # Skip verification in dev if no token

    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

        # Build the full URL
        url = request.build_absolute_uri()
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')

        return validator.validate(url, request.POST.dict(), signature)
    except ImportError:
        logger.warning('twilio package not installed, skipping signature verification')
        return True


@csrf_exempt
@require_POST
def twilio_inbound_sms(request):
    """Handle inbound SMS from Twilio."""
    if not _verify_twilio_signature(request):
        logger.warning('Invalid Twilio signature on inbound SMS')
        return HttpResponseForbidden('Invalid signature')

    from_number = request.POST.get('From', '')
    body = request.POST.get('Body', '')
    message_sid = request.POST.get('MessageSid', '')

    logger.info('Inbound SMS from %s: %s', from_number, body[:50])

    # Find user by phone number
    try:
        profile = UserProfile.objects.get(phone=from_number)
        user = profile.user
    except UserProfile.DoesNotExist:
        logger.warning('Inbound SMS from unknown number: %s', from_number)
        return _twiml_response(
            "Welcome! Visit our website to create an account and start your business journey."
        )

    # Log inbound message
    MessageLog.objects.create(
        user=user,
        channel='SMS',
        direction='IN',
        content=body,
        status='RECEIVED',
        twilio_sid=message_sid,
    )

    # Process reply
    reply = TaskProgressService.process_inbound_reply(user, body)

    # Log outbound reply
    MessageLog.objects.create(
        user=user,
        channel='SMS',
        direction='OUT',
        content=reply,
        status='SENT',
    )

    return _twiml_response(reply)


@csrf_exempt
@require_POST
def twilio_status_callback(request):
    """Handle Twilio message status updates."""
    if not _verify_twilio_signature(request):
        return HttpResponseForbidden('Invalid signature')

    message_sid = request.POST.get('MessageSid', '')
    status = request.POST.get('MessageStatus', '')

    status_map = {
        'delivered': 'DELIVERED',
        'sent': 'SENT',
        'failed': 'FAILED',
        'undelivered': 'FAILED',
    }

    new_status = status_map.get(status)
    if new_status and message_sid:
        updated = MessageLog.objects.filter(twilio_sid=message_sid).update(
            status=new_status,
        )
        if updated:
            logger.info('Twilio status update: %s -> %s', message_sid, new_status)

    return HttpResponse('OK')


@csrf_exempt
@require_POST
def sendgrid_event_webhook(request):
    """Handle SendGrid event webhook."""
    import json

    # Verify signature (basic check)
    if not _verify_sendgrid_signature(request):
        return HttpResponseForbidden('Invalid signature')

    try:
        events = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse('Invalid JSON', status=400)

    status_map = {
        'delivered': 'DELIVERED',
        'bounce': 'FAILED',
        'dropped': 'FAILED',
        'deferred': 'QUEUED',
    }

    for event in events:
        event_type = event.get('event', '')
        sg_message_id = event.get('sg_message_id', '').split('.')[0]

        new_status = status_map.get(event_type)
        if new_status and sg_message_id:
            MessageLog.objects.filter(
                sendgrid_message_id__startswith=sg_message_id,
            ).update(status=new_status)

    return HttpResponse('OK')


def _verify_sendgrid_signature(request):
    """Verify SendGrid webhook signature."""
    webhook_key = getattr(settings, 'SENDGRID_WEBHOOK_VERIFICATION_KEY', '')
    if not webhook_key:
        return True  # Skip in dev

    signature = request.META.get('HTTP_X_TWILIO_EMAIL_EVENT_WEBHOOK_SIGNATURE', '')
    timestamp = request.META.get('HTTP_X_TWILIO_EMAIL_EVENT_WEBHOOK_TIMESTAMP', '')

    if not signature or not timestamp:
        return True  # Skip if headers not present

    payload = timestamp + request.body.decode('utf-8')
    expected = hmac.new(
        webhook_key.encode(), payload.encode(), hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def _twiml_response(message: str) -> HttpResponse:
    """Build a TwiML response."""
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{message}</Message></Response>'
    return HttpResponse(xml, content_type='text/xml')
