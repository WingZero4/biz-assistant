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


STEP3_STAGE_CONFIG = {
    'IDEA': {
        'title': 'Your Skills & Experience',
        'skills_label': 'What skills do you have?',
        'experience_label': 'Business experience level',
        'hours_label': 'Hours you can dedicate per day',
        'hours_help': 'How many hours daily can you spend building this business?',
        'education_placeholder': 'e.g. MBA, Self-taught, Marketing degree',
    },
    'PLANNING': {
        'title': 'Your Skills & Experience',
        'skills_label': 'What skills do you bring?',
        'experience_label': 'Business experience level',
        'hours_label': 'Hours you can dedicate per day',
        'hours_help': 'How many hours daily can you spend on launch tasks?',
        'education_placeholder': 'e.g. MBA, Self-taught, Marketing degree',
    },
    'EARLY': {
        'title': 'Your Skills & Experience',
        'skills_label': 'What skills do you use in your business?',
        'experience_label': 'Your business experience',
        'hours_label': 'Hours you can dedicate to growth per day',
        'hours_help': 'Beyond day-to-day operations, how many hours can you spend on growth?',
        'education_placeholder': 'e.g. MBA, Industry certification, Self-taught',
    },
    'GROWING': {
        'title': 'Your Team & Expertise',
        'skills_label': 'What are your strongest skills?',
        'experience_label': 'Your business experience',
        'hours_label': 'Hours you can dedicate to strategic work per day',
        'hours_help': 'Beyond running daily operations, how many hours for strategic initiatives?',
        'education_placeholder': 'e.g. MBA, Industry certification, 10+ years in field',
    },
    'ESTABLISHED': {
        'title': 'Your Team & Expertise',
        'skills_label': 'What are your core competencies?',
        'experience_label': 'Your business experience',
        'hours_label': 'Hours you can dedicate to this initiative per day',
        'hours_help': 'How many hours daily can you dedicate to the improvements you want?',
        'education_placeholder': 'e.g. MBA, Executive education, Industry veteran',
    },
}


class SkillsExperienceForm(forms.Form):
    """Step 3: Skills and experience — adapts to business stage."""
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

    def __init__(self, *args, stage='IDEA', **kwargs):
        super().__init__(*args, **kwargs)
        config = STEP3_STAGE_CONFIG.get(stage, STEP3_STAGE_CONFIG['IDEA'])

        self.fields['owner_skills'].label = config['skills_label']
        self.fields['business_experience'].label = config['experience_label']
        self.fields['hours_per_day'].label = config['hours_label']
        self.fields['hours_per_day'].help_text = config['hours_help']
        self.fields['education_background'].widget.attrs['placeholder'] = config['education_placeholder']

        self.stage_title = config['title']


STEP4_STAGE_CONFIG = {
    'IDEA': {
        'title': 'Industry & Competition',
        'niche_label': 'Specific niche',
        'niche_placeholder': 'e.g. Vegan bakery, B2B SaaS for dentists',
        'model_label': 'Planned business model',
        'usp_label': 'What will make you different?',
        'usp_placeholder': 'What will set you apart from competitors?',
        'competitors_label': 'Known competitors',
        'competitors_placeholder': 'List any competitors you know (one per line)',
        'budget_label': 'Startup budget',
        'location_placeholder': 'City, State or "Online only"',
    },
    'PLANNING': {
        'title': 'Industry & Competition',
        'niche_label': 'Specific niche',
        'niche_placeholder': 'e.g. Vegan bakery, B2B SaaS for dentists',
        'model_label': 'Business model',
        'usp_label': 'What will make you different?',
        'usp_placeholder': 'What will set your business apart from competitors?',
        'competitors_label': 'Known competitors',
        'competitors_placeholder': 'List competitors you\'ve researched (one per line)',
        'budget_label': 'Launch budget',
        'location_placeholder': 'City, State or "Online only"',
    },
    'EARLY': {
        'title': 'Your Market Position',
        'niche_label': 'Your niche',
        'niche_placeholder': 'e.g. Organic pet food in Austin, B2B SaaS for dentists',
        'model_label': 'Business model',
        'usp_label': 'What makes you different?',
        'usp_placeholder': 'What do customers say sets you apart?',
        'competitors_label': 'Main competitors',
        'competitors_placeholder': 'Who are you competing against? (one per line)',
        'budget_label': 'Budget for growth',
        'location_placeholder': 'City, State or "Online only"',
    },
    'GROWING': {
        'title': 'Your Market Position',
        'niche_label': 'Your market niche',
        'niche_placeholder': 'e.g. Premium organic pet food, Enterprise HR SaaS',
        'model_label': 'Primary business model',
        'usp_label': 'Your competitive advantage',
        'usp_placeholder': 'What keeps customers choosing you over competitors?',
        'competitors_label': 'Key competitors',
        'competitors_placeholder': 'Your main competitors (one per line)',
        'budget_label': 'Budget for this initiative',
        'location_placeholder': 'Primary market / City, State',
    },
    'ESTABLISHED': {
        'title': 'Your Market Position',
        'niche_label': 'Your market segment',
        'niche_placeholder': 'e.g. Premium organic pet food, Enterprise HR SaaS',
        'model_label': 'Primary business model',
        'usp_label': 'Your competitive advantage',
        'usp_placeholder': 'What is your moat? Why do customers stay?',
        'competitors_label': 'Key competitors',
        'competitors_placeholder': 'Your main competitors and emerging threats (one per line)',
        'budget_label': 'Budget for this initiative',
        'location_placeholder': 'Primary market / Headquarters',
    },
}


class IndustryDetailsForm(forms.Form):
    """Step 4: Industry and competition — adapts to business stage."""
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

    def __init__(self, *args, stage='IDEA', **kwargs):
        super().__init__(*args, **kwargs)
        config = STEP4_STAGE_CONFIG.get(stage, STEP4_STAGE_CONFIG['IDEA'])

        self.fields['niche'].label = config['niche_label']
        self.fields['niche'].widget.attrs['placeholder'] = config['niche_placeholder']
        self.fields['business_model'].label = config['model_label']
        self.fields['unique_selling_point'].label = config['usp_label']
        self.fields['unique_selling_point'].widget.attrs['placeholder'] = config['usp_placeholder']
        self.fields['known_competitors'].label = config['competitors_label']
        self.fields['known_competitors'].widget.attrs['placeholder'] = config['competitors_placeholder']
        self.fields['budget_range'].label = config['budget_label']
        self.fields['location'].widget.attrs['placeholder'] = config['location_placeholder']

        self.stage_title = config['title']


STEP5_STAGE_CONFIG = {
    'IDEA': {
        'title': 'Your Digital Presence',
        'website_label': 'I have a website',
        'domain_label': 'I own a domain name',
        'branding_label': 'I have a logo / brand identity',
        'social_label': 'I have social media accounts',
        'platforms_label': 'Which platforms?',
        'email_label': 'I have an email list',
    },
    'PLANNING': {
        'title': 'Your Digital Presence',
        'website_label': 'I have a website',
        'domain_label': 'I own a domain name',
        'branding_label': 'I have a logo / brand identity',
        'social_label': 'I have social media accounts',
        'platforms_label': 'Which platforms?',
        'email_label': 'I have an email list',
    },
    'EARLY': {
        'title': 'Your Current Digital Setup',
        'website_label': 'I have a business website',
        'domain_label': 'I have a custom domain',
        'branding_label': 'I have professional branding (logo, colors)',
        'social_label': 'I have active social media accounts',
        'platforms_label': 'Which platforms are you active on?',
        'email_label': 'I have an email list or newsletter',
    },
    'GROWING': {
        'title': 'Your Digital Assets',
        'website_label': 'We have a business website',
        'domain_label': 'We have a custom domain',
        'branding_label': 'We have professional branding',
        'social_label': 'We have active social media',
        'platforms_label': 'Which platforms are you active on?',
        'email_label': 'We have an email list or newsletter',
    },
    'ESTABLISHED': {
        'title': 'Your Digital Assets',
        'website_label': 'We have a business website',
        'domain_label': 'We have a custom domain',
        'branding_label': 'We have established branding',
        'social_label': 'We have active social media',
        'platforms_label': 'Which platforms are you active on?',
        'email_label': 'We have an email list or newsletter',
    },
}


class DigitalPresenceForm(forms.Form):
    """Step 5: Current digital presence — adapts to business stage."""
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

    def __init__(self, *args, stage='IDEA', **kwargs):
        super().__init__(*args, **kwargs)
        config = STEP5_STAGE_CONFIG.get(stage, STEP5_STAGE_CONFIG['IDEA'])

        self.fields['has_website'].label = config['website_label']
        self.fields['has_domain'].label = config['domain_label']
        self.fields['has_branding'].label = config['branding_label']
        self.fields['has_social_media'].label = config['social_label']
        self.fields['social_platforms'].label = config['platforms_label']
        self.fields['has_email_list'].label = config['email_label']

        self.stage_title = config['title']
