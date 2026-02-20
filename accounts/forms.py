from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(
        max_length=20, required=False,
        help_text='E.164 format, e.g. +15551234567',
        widget=forms.TextInput(attrs={'placeholder': '+15551234567'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # UserProfile is auto-created by signal, update phone
            if self.cleaned_data.get('phone'):
                user.profile.phone = self.cleaned_data['phone']
                user.profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'timezone', 'preferred_channel', 'daily_send_hour']
        widgets = {
            'daily_send_hour': forms.NumberInput(attrs={'min': 0, 'max': 23}),
        }
