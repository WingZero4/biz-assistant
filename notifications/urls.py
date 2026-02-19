from django.urls import path

from . import webhooks

app_name = 'notifications'

urlpatterns = [
    path('twilio/inbound/', webhooks.twilio_inbound_sms, name='twilio_inbound'),
    path('twilio/status/', webhooks.twilio_status_callback, name='twilio_status'),
    path('sendgrid/events/', webhooks.sendgrid_event_webhook, name='sendgrid_events'),
]
