from django.contrib.auth.models import User
from django.db import models

from onboarding.models import BusinessProfile


class TaskPlan(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('PAUSED', 'Paused'),
        ('REPLACED', 'Replaced by new plan'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='task_plans',
    )
    business_profile = models.ForeignKey(
        BusinessProfile, on_delete=models.CASCADE, related_name='task_plans',
    )
    title = models.CharField(max_length=255, default='30-Day Launch Plan')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='ACTIVE',
    )
    phase = models.PositiveSmallIntegerField(default=1)
    duration_days = models.PositiveSmallIntegerField(default=30)
    starts_on = models.DateField()
    ends_on = models.DateField()
    ai_generation_metadata = models.JSONField(
        default=dict, blank=True,
        help_text='Model, prompt tokens, generation params',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} for {self.user.username}'

    @property
    def completion_pct(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        done = self.tasks.filter(status='DONE').count()
        return round((done / total) * 100)


class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent to user'),
        ('DONE', 'Completed'),
        ('SKIPPED', 'Skipped'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    CATEGORY_CHOICES = [
        ('LEGAL', 'Legal & Registration'),
        ('FINANCE', 'Finance & Accounting'),
        ('MARKETING', 'Marketing & Branding'),
        ('PRODUCT', 'Product & Service'),
        ('SALES', 'Sales & Customers'),
        ('OPERATIONS', 'Operations & Setup'),
        ('DIGITAL', 'Digital Presence'),
        ('PLANNING', 'Strategy & Planning'),
    ]
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy (< 30 min)'),
        ('MEDIUM', 'Medium (30-90 min)'),
        ('HARD', 'Hard (2+ hours)'),
    ]

    plan = models.ForeignKey(
        TaskPlan, on_delete=models.CASCADE, related_name='tasks',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM',
    )
    estimated_minutes = models.PositiveSmallIntegerField(default=30)
    day_number = models.PositiveSmallIntegerField(
        help_text='Which day in the plan (1-30) this task is scheduled for',
    )
    due_date = models.DateField()
    sort_order = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='PENDING',
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    skipped_at = models.DateTimeField(null=True, blank=True)
    user_response = models.TextField(blank=True)
    rescheduled_to = models.DateField(null=True, blank=True)

    # AI fields
    personalized_message = models.TextField(
        blank=True,
        help_text='AI-generated motivational message sent with this task',
    )
    ai_notes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['due_date', 'sort_order']

    def __str__(self):
        return f'Day {self.day_number}: {self.title} [{self.status}]'
