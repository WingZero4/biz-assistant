from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def twilio_inbound_sms(request):
    # TODO: Sprint 6 — Twilio inbound SMS handler + signature verification
    return HttpResponse('<Response></Response>', content_type='text/xml')


@csrf_exempt
def twilio_status_callback(request):
    # TODO: Sprint 6 — Twilio delivery status callback
    return HttpResponse('OK')


@csrf_exempt
def sendgrid_event_webhook(request):
    # TODO: Sprint 6 — SendGrid event webhook handler
    return HttpResponse('OK')
