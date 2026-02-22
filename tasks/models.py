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
    previous_plan = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='next_plans',
    )
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

    @property
    def is_overdue(self):
        from django.utils import timezone
        return (
            self.status in ('PENDING', 'SENT')
            and self.due_date < timezone.now().date()
        )

    def __str__(self):
        return f'Day {self.day_number}: {self.title} [{self.status}]'


class Achievement(models.Model):
    BADGE_CHOICES = [
        ('FIRST_TASK', 'First Task Completed'),
        ('FIRST_WEEK', 'First Week Complete'),
        ('STREAK_3', '3-Day Streak'),
        ('STREAK_7', '7-Day Streak'),
        ('STREAK_14', '14-Day Streak'),
        ('STREAK_30', '30-Day Streak'),
        ('HALF_PLAN', 'Halfway Through Plan'),
        ('PLAN_COMPLETE', 'Plan Completed'),
        ('CATEGORY_MASTER', 'Category Master'),
        ('SPEED_DEMON', 'Speed Demon'),
        ('COMEBACK', 'Comeback Kid'),
        ('MULTI_PLAN', 'Multi-Plan Veteran'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='achievements',
    )
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-earned_at']

    def __str__(self):
        return f'{self.title} ({self.user.username})'


class StreakRecord(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='streak_records',
    )
    date = models.DateField()
    tasks_completed = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [('user', 'date')]
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} — {self.date} ({self.tasks_completed} tasks)'


RESOURCE_TYPE_CHOICES = [
    ('TEMPLATE', 'Template'),
    ('CHECKLIST', 'Checklist'),
    ('GUIDE', 'Reference Guide'),
    ('LINK', 'External Link'),
    ('WORKSHEET', 'Worksheet'),
]


class ResourceTemplate(models.Model):
    """Reusable resource library — grows from AI-generated drafts."""
    STATUS_CHOICES = [
        ('DRAFT', 'AI-Generated Draft'),
        ('REVIEWED', 'Reviewed & Approved'),
        ('ARCHIVED', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPE_CHOICES)
    content = models.TextField(
        blank=True, help_text='Template/guide/checklist content (markdown)',
    )
    external_url = models.URLField(blank=True)
    business_types = models.JSONField(
        default=list, blank=True,
        help_text='Business types this applies to, e.g. ["bakery", "restaurant"]',
    )
    categories = models.JSONField(
        default=list, blank=True,
        help_text='Task categories: ["LEGAL", "MARKETING"]',
    )
    tags = models.JSONField(
        default=list, blank=True,
        help_text='Freeform tags for search: ["llc", "texas"]',
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='DRAFT',
    )
    times_used = models.PositiveIntegerField(default=0)
    ai_model_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-times_used', '-created_at']

    def __str__(self):
        return f'[{self.get_resource_type_display()}] {self.title} ({self.get_status_display()})'


class TaskResource(models.Model):
    """Resource attached to a specific task for a specific user."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='resources')
    template = models.ForeignKey(
        ResourceTemplate, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='usages',
    )
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPE_CHOICES)
    content = models.TextField(blank=True)
    external_url = models.URLField(blank=True)
    is_completed = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.get_resource_type_display()}: {self.title}'
