from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    CHANNEL_CHOICES = [
        ('BOTH', 'SMS + Email'),
        ('SMS', 'SMS Only'),
        ('EMAIL', 'Email Only'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(
        max_length=20, blank=True,
        help_text='E.164 format, e.g. +15551234567',
    )
    timezone = models.CharField(max_length=50, default='America/New_York')
    preferred_channel = models.CharField(
        max_length=5, choices=CHANNEL_CHOICES, default='BOTH',
    )
    daily_send_hour = models.PositiveSmallIntegerField(
        default=8,
        help_text='Hour (0-23) in user timezone to send daily tasks',
    )
    is_onboarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} profile'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
