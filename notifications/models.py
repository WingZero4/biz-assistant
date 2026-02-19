from django.contrib.auth.models import User
from django.db import models


class MessageLog(models.Model):
    CHANNEL_CHOICES = [
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
    ]
    DIRECTION_CHOICES = [
        ('OUT', 'Outbound'),
        ('IN', 'Inbound'),
    ]
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('RECEIVED', 'Received'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='message_logs',
    )
    channel = models.CharField(max_length=5, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    content = models.TextField()
    subject = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='QUEUED',
    )
    twilio_sid = models.CharField(max_length=50, blank=True, db_index=True)
    sendgrid_message_id = models.CharField(
        max_length=100, blank=True, db_index=True,
    )
    error_message = models.TextField(blank=True)
    related_task = models.ForeignKey(
        'tasks.Task', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='messages',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.channel} {self.direction} to {self.user.username} [{self.status}]'
