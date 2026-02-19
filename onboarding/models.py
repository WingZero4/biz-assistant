from django.contrib.auth.models import User
from django.db import models


class BusinessProfile(models.Model):
    STAGE_CHOICES = [
        ('IDEA', 'Just an Idea'),
        ('PLANNING', 'Planning Stage'),
        ('EARLY', 'Early Stage (0-6 months)'),
        ('GROWING', 'Growing (6-24 months)'),
        ('ESTABLISHED', 'Established (2+ years)'),
    ]
    BUDGET_CHOICES = [
        ('BOOTSTRAP', '$0 - Bootstrap'),
        ('LOW', '$1 - $1,000'),
        ('MEDIUM', '$1,000 - $10,000'),
        ('HIGH', '$10,000+'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='business_profile',
    )
    business_name = models.CharField(max_length=255)
    business_type = models.CharField(
        max_length=100,
        help_text='e.g. E-commerce, Consulting, Restaurant, SaaS',
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    description = models.TextField(
        blank=True, help_text='Brief description of the business idea',
    )
    goals = models.JSONField(
        default=list, help_text='List of primary goals',
    )
    target_audience = models.TextField(blank=True)
    budget_range = models.CharField(
        max_length=20, choices=BUDGET_CHOICES, default='BOOTSTRAP',
    )
    location = models.CharField(
        max_length=255, blank=True,
        help_text='City/state or "Online only"',
    )

    # AI-generated fields
    ai_assessment = models.JSONField(
        default=dict, blank=True,
        help_text='Claude-generated business assessment JSON',
    )
    ai_model_used = models.CharField(max_length=50, blank=True)
    assessment_generated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.business_name} ({self.user.username})'


class Conversation(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conversations',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text='Token usage, model info, step number',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'
