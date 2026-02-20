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


class BusinessDetailsForm(forms.Form):
    """Step 3: Budget and location."""
    budget_range = forms.ChoiceField(choices=BusinessProfile.BUDGET_CHOICES)
    location = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'City, State or "Online only"',
        }),
    )
