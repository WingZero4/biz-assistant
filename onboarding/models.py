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
    EXPERIENCE_CHOICES = [
        ('NONE', 'No business experience'),
        ('SOME', 'Some experience (side projects, freelance)'),
        ('EXPERIENCED', 'Experienced (ran a business before)'),
        ('SERIAL', 'Serial entrepreneur'),
    ]
    MODEL_CHOICES = [
        ('PRODUCT', 'Physical/Digital Products'),
        ('SERVICE', 'Services'),
        ('SUBSCRIPTION', 'Subscription/Membership'),
        ('MARKETPLACE', 'Marketplace/Platform'),
        ('HYBRID', 'Hybrid/Multiple'),
    ]
    SKILL_CHOICES = [
        ('social_media', 'Social Media'),
        ('design', 'Graphic Design'),
        ('coding', 'Coding/Tech'),
        ('sales', 'Sales'),
        ('accounting', 'Accounting/Finance'),
        ('marketing', 'Marketing'),
        ('writing', 'Writing/Content'),
        ('photography', 'Photography/Video'),
    ]
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'X / Twitter'),
        ('youtube', 'YouTube'),
        ('pinterest', 'Pinterest'),
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

    # Skills & Experience
    owner_skills = models.JSONField(
        default=list, blank=True,
        help_text='List of skill keys from SKILL_CHOICES',
    )
    business_experience = models.CharField(
        max_length=20, choices=EXPERIENCE_CHOICES, default='NONE',
    )
    hours_per_day = models.PositiveSmallIntegerField(
        default=2, help_text='Hours available per day (1-8)',
    )
    education_background = models.CharField(max_length=255, blank=True)

    # Industry Details
    niche = models.CharField(
        max_length=255, blank=True,
        help_text='Specific sub-niche, e.g. "vegan bakery", "B2B SaaS"',
    )
    known_competitors = models.JSONField(
        default=list, blank=True,
        help_text='Competitor names they already know',
    )
    unique_selling_point = models.TextField(
        blank=True, help_text='What makes this business different',
    )
    business_model = models.CharField(
        max_length=20, choices=MODEL_CHOICES, default='PRODUCT',
    )

    # Stage-specific context
    current_revenue = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Revenue bracket for existing businesses',
    )
    team_size = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Team size for growing/established businesses',
    )
    biggest_challenges = models.TextField(
        blank=True, default='',
        help_text='Current challenges (for existing businesses)',
    )

    # Digital Presence
    has_website = models.BooleanField(default=False)
    has_social_media = models.BooleanField(default=False)
    social_platforms = models.JSONField(
        default=list, blank=True,
        help_text='Platform keys from PLATFORM_CHOICES',
    )
    has_email_list = models.BooleanField(default=False)
    has_domain = models.BooleanField(default=False)
    has_branding = models.BooleanField(default=False)

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


class WeeklyPulse(models.Model):
    ENERGY_CHOICES = [
        (1, 'Exhausted'),
        (2, 'Low energy'),
        (3, 'Normal'),
        (4, 'Energized'),
        (5, 'On fire'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='weekly_pulses',
    )
    business_profile = models.ForeignKey(
        BusinessProfile, on_delete=models.CASCADE, related_name='weekly_pulses',
    )
    week_of = models.DateField(help_text='Monday of the week')
    revenue_this_week = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    new_customers = models.PositiveSmallIntegerField(default=0)
    hours_worked = models.PositiveSmallIntegerField(default=0)
    energy_level = models.PositiveSmallIntegerField(
        choices=ENERGY_CHOICES, default=3,
    )
    biggest_win = models.TextField(blank=True)
    biggest_blocker = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'week_of')]
        ordering = ['-week_of']

    def __str__(self):
        return f'{self.user.username} — Week of {self.week_of}'


class Conversation(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    TYPE_CHOICES = [
        ('SYSTEM', 'System'),
        ('CHAT', 'Chat'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conversations',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    conversation_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default='SYSTEM',
    )
    session_id = models.CharField(max_length=36, blank=True, db_index=True)
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text='Token usage, model info, step number',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'


class GeneratedDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('SOCIAL_POST', 'Social Media Post'),
        ('EMAIL_CAMPAIGN', 'Email Campaign'),
        ('BIZ_PLAN_OUTLINE', 'Business Plan Outline'),
        ('ELEVATOR_PITCH', 'Elevator Pitch'),
        ('PRODUCT_DESCRIPTION', 'Product Description'),
        ('JOB_POSTING', 'Job Posting'),
        ('CUSTOMER_EMAIL', 'Customer Email'),
        ('AD_COPY', 'Ad Copy'),
        ('BLOG_POST', 'Blog Post Outline'),
    ]
    PLATFORM_CHOICES = [
        ('', 'General'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'X / Twitter'),
        ('tiktok', 'TikTok'),
        ('email', 'Email'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='generated_documents',
    )
    business_profile = models.ForeignKey(
        BusinessProfile, on_delete=models.CASCADE, related_name='generated_documents',
    )
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    platform = models.CharField(max_length=20, blank=True, choices=PLATFORM_CHOICES)
    title = models.CharField(max_length=255)
    prompt_used = models.TextField(blank=True)
    content = models.TextField()
    is_favorite = models.BooleanField(default=False)
    ai_model_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_doc_type_display()}: {self.title}'
