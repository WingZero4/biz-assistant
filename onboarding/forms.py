from django import forms

from .models import BusinessProfile


class BusinessBasicsForm(forms.Form):
    """Step 1: Business basics."""
    business_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Sunrise Bakery'}),
    )
    business_type = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Bakery, Consulting, E-commerce, SaaS',
        }),
    )
    stage = forms.ChoiceField(choices=BusinessProfile.STAGE_CHOICES)


# Stage-specific configuration for Step 2
STAGE_CONFIG = {
    'IDEA': {
        'title': 'Tell us about your idea',
        'description_label': 'Describe your business idea',
        'description_placeholder': 'What product or service will you offer? Who is it for?',
        'goals_label': 'What do you want to achieve?',
        'goals_placeholder': 'e.g. Validate my idea\nGet my first 10 customers\nLaunch within 30 days',
        'goals_help': 'Enter one goal per line.',
        'audience_label': 'Who is your ideal customer?',
        'audience_placeholder': 'Describe your target customer — age, interests, problems they have...',
        'show_revenue': False,
        'show_employees': False,
        'show_challenges': False,
    },
    'PLANNING': {
        'title': 'Tell us about your plans',
        'description_label': 'What will your business do?',
        'description_placeholder': 'Describe the product/service you\'re planning to launch...',
        'goals_label': 'What are your launch goals?',
        'goals_placeholder': 'e.g. Register my business\nBuild a website\nMake my first sale',
        'goals_help': 'Enter one goal per line.',
        'audience_label': 'Who will you sell to?',
        'audience_placeholder': 'Describe your target market — demographics, location, needs...',
        'show_revenue': False,
        'show_employees': False,
        'show_challenges': False,
    },
    'EARLY': {
        'title': 'Tell us about your business',
        'description_label': 'What does your business do?',
        'description_placeholder': 'Describe your products/services and how you deliver them...',
        'goals_label': 'What are your growth goals?',
        'goals_placeholder': 'e.g. Reach $5K monthly revenue\nHire my first employee\nExpand to new markets',
        'goals_help': 'Enter one goal per line.',
        'audience_label': 'Who are your current customers?',
        'audience_placeholder': 'Describe who buys from you today — what do they have in common?',
        'show_revenue': True,
        'show_employees': False,
        'show_challenges': True,
    },
    'GROWING': {
        'title': 'Tell us about your business',
        'description_label': 'What does your business do?',
        'description_placeholder': 'Describe your business, products/services, and what makes you successful...',
        'goals_label': 'What are your next milestones?',
        'goals_placeholder': 'e.g. Scale to $50K/month\nBuild a team of 5\nLaunch a second product line',
        'goals_help': 'Enter one goal per line.',
        'audience_label': 'Who is your core customer segment?',
        'audience_placeholder': 'Describe your best customers and the segments you want to expand into...',
        'show_revenue': True,
        'show_employees': True,
        'show_challenges': True,
    },
    'ESTABLISHED': {
        'title': 'Tell us about your business',
        'description_label': 'What does your business do?',
        'description_placeholder': 'Describe your business, market position, and key offerings...',
        'goals_label': 'What are you looking to improve?',
        'goals_placeholder': 'e.g. Optimize operations\nEnter a new market\nImprove profit margins\nDigital transformation',
        'goals_help': 'Enter one goal per line.',
        'audience_label': 'Who are your primary customer segments?',
        'audience_placeholder': 'Describe your main customer types and any new segments you\'re targeting...',
        'show_revenue': True,
        'show_employees': True,
        'show_challenges': True,
    },
}

REVENUE_CHOICES = [
    ('PRE_REVENUE', 'Pre-revenue'),
    ('UNDER_1K', 'Under $1,000/month'),
    ('1K_5K', '$1,000 - $5,000/month'),
    ('5K_20K', '$5,000 - $20,000/month'),
    ('20K_PLUS', '$20,000+/month'),
]

EMPLOYEE_CHOICES = [
    ('SOLO', 'Just me'),
    ('2_5', '2-5 people'),
    ('6_20', '6-20 people'),
    ('20_PLUS', '20+ people'),
]


class BusinessGoalsForm(forms.Form):
    """Step 2: Goals and context — adapts to business stage."""
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
    )
    goals = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    target_audience = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
    )
    current_revenue = forms.ChoiceField(
        choices=REVENUE_CHOICES,
        required=False,
        label='Current monthly revenue',
    )
    team_size = forms.ChoiceField(
        choices=EMPLOYEE_CHOICES,
        required=False,
        label='Team size',
    )
    biggest_challenges = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'What are the biggest obstacles you face right now?',
        }),
        required=False,
        label='Biggest challenges',
    )

    def __init__(self, *args, stage='IDEA', **kwargs):
        super().__init__(*args, **kwargs)
        config = STAGE_CONFIG.get(stage, STAGE_CONFIG['IDEA'])

        # Update labels and placeholders from stage config
        self.fields['description'].label = config['description_label']
        self.fields['description'].widget.attrs['placeholder'] = config['description_placeholder']

        self.fields['goals'].label = config['goals_label']
        self.fields['goals'].widget.attrs['placeholder'] = config['goals_placeholder']
        self.fields['goals'].help_text = config['goals_help']

        self.fields['target_audience'].label = config['audience_label']
        self.fields['target_audience'].widget.attrs['placeholder'] = config['audience_placeholder']

        # Show/hide stage-specific fields
        if not config['show_revenue']:
            del self.fields['current_revenue']
        if not config['show_employees']:
            del self.fields['team_size']
        if not config['show_challenges']:
            del self.fields['biggest_challenges']

        # Store title for template
        self.stage_title = config['title']


class SkillsExperienceForm(forms.Form):
    """Step 3: Skills and experience."""
    owner_skills = forms.MultipleChoiceField(
        choices=BusinessProfile.SKILL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='What skills do you have?',
    )
    business_experience = forms.ChoiceField(
        choices=BusinessProfile.EXPERIENCE_CHOICES,
        label='Business experience level',
    )
    hours_per_day = forms.IntegerField(
        min_value=1, max_value=8, initial=2,
        label='Hours you can dedicate per day',
        widget=forms.NumberInput(attrs={'placeholder': '2'}),
    )
    education_background = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. MBA, Self-taught, Marketing degree',
        }),
        label='Education (optional)',
    )


class IndustryDetailsForm(forms.Form):
    """Step 4: Industry and competition."""
    niche = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Vegan bakery, B2B SaaS for dentists',
        }),
        label='Specific niche',
    )
    business_model = forms.ChoiceField(
        choices=BusinessProfile.MODEL_CHOICES,
        label='Business model',
    )
    unique_selling_point = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'What makes your business different from competitors?',
        }),
        required=False,
        label='Unique selling point',
    )
    known_competitors = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'List any competitors you know (one per line)',
        }),
        required=False,
        label='Known competitors',
    )
    budget_range = forms.ChoiceField(choices=BusinessProfile.BUDGET_CHOICES)
    location = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'City, State or "Online only"',
        }),
    )


class DigitalPresenceForm(forms.Form):
    """Step 5: Current digital presence."""
    has_website = forms.BooleanField(required=False, label='I have a website')
    has_domain = forms.BooleanField(required=False, label='I own a domain name')
    has_branding = forms.BooleanField(required=False, label='I have a logo / brand identity')
    has_social_media = forms.BooleanField(required=False, label='I have social media accounts')
    social_platforms = forms.MultipleChoiceField(
        choices=BusinessProfile.PLATFORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Which platforms?',
    )
    has_email_list = forms.BooleanField(required=False, label='I have an email list')
