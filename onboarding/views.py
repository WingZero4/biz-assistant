from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    BusinessBasicsForm,
    BusinessGoalsForm,
    DigitalPresenceForm,
    IndustryDetailsForm,
    SkillsExperienceForm,
)
from .services import OnboardingService

TOTAL_STEPS = 6


def _get_wizard_data(request):
    return request.session.get('onboarding_data', {})


def _save_wizard_data(request, step_data):
    data = _get_wizard_data(request)
    data.update(step_data)
    request.session['onboarding_data'] = data


def _has_basics(request):
    return bool(_get_wizard_data(request).get('business_name'))


@login_required
def wizard_step_1(request):
    if request.method == 'POST':
        form = BusinessBasicsForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_2')
    else:
        form = BusinessBasicsForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_1.html', {
        'form': form, 'step': 1, 'total_steps': TOTAL_STEPS,
        'step_title': 'Business Basics',
    })


@login_required
def wizard_step_2(request):
    if not _has_basics(request):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        form = BusinessGoalsForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_3')
    else:
        form = BusinessGoalsForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_2.html', {
        'form': form, 'step': 2, 'total_steps': TOTAL_STEPS,
        'step_title': 'Goals & Audience',
    })


@login_required
def wizard_step_3(request):
    if not _has_basics(request):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        form = SkillsExperienceForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_4')
    else:
        form = SkillsExperienceForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_3.html', {
        'form': form, 'step': 3, 'total_steps': TOTAL_STEPS,
        'step_title': 'Skills & Experience',
    })


@login_required
def wizard_step_4(request):
    if not _has_basics(request):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        form = IndustryDetailsForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_5')
    else:
        form = IndustryDetailsForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_4.html', {
        'form': form, 'step': 4, 'total_steps': TOTAL_STEPS,
        'step_title': 'Industry & Competition',
    })


@login_required
def wizard_step_5(request):
    if not _has_basics(request):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        form = DigitalPresenceForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_6')
    else:
        form = DigitalPresenceForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_5.html', {
        'form': form, 'step': 5, 'total_steps': TOTAL_STEPS,
        'step_title': 'Digital Presence',
    })


@login_required
def wizard_step_6(request):
    """Review step — show summary, run AI assessment, generate plan."""
    data = _get_wizard_data(request)
    if not data.get('business_name'):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        profile = OnboardingService.create_business_profile(request.user, data)
        OnboardingService.run_ai_assessment(profile)
        OnboardingService.generate_initial_plan(profile)
        OnboardingService.complete_onboarding(request.user)
        request.session.pop('onboarding_data', None)
        return redirect('onboarding:complete')

    # Parse goals for display
    goals_text = data.get('goals', '')
    goals_list = [g.strip() for g in goals_text.split('\n') if g.strip()]

    # Skill labels for display
    skill_map = dict(BusinessBasicsForm.Meta.model.SKILL_CHOICES) if hasattr(BusinessBasicsForm, 'Meta') else {}
    from .models import BusinessProfile
    skill_map = dict(BusinessProfile.SKILL_CHOICES)
    platform_map = dict(BusinessProfile.PLATFORM_CHOICES)
    skills_display = [skill_map.get(s, s) for s in data.get('owner_skills', [])]
    platforms_display = [platform_map.get(p, p) for p in data.get('social_platforms', [])]

    return render(request, 'onboarding/step_6.html', {
        'data': data,
        'goals_list': goals_list,
        'skills_display': skills_display,
        'platforms_display': platforms_display,
        'step': 6, 'total_steps': TOTAL_STEPS,
        'step_title': 'Review & Launch',
    })


@login_required
def onboarding_complete(request):
    profile = getattr(request.user, 'business_profile', None)
    assessment = profile.ai_assessment if profile else {}
    return render(request, 'onboarding/complete.html', {
        'profile': profile,
        'assessment': assessment,
    })
