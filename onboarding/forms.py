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


class BusinessGoalsForm(forms.Form):
    """Step 2: Goals and target audience."""
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Briefly describe your business idea...',
        }),
        required=False,
    )
    goals = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'What are your top goals? (one per line)',
        }),
        help_text='Enter one goal per line.',
    )
    target_audience = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Who is your ideal customer?',
        }),
        required=False,
    )


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
