from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BusinessBasicsForm, BusinessDetailsForm, BusinessGoalsForm
from .services import OnboardingService

WIZARD_STEPS = {
    1: ('Business Basics', BusinessBasicsForm),
    2: ('Goals & Audience', BusinessGoalsForm),
    3: ('Budget & Location', BusinessDetailsForm),
}


def _get_wizard_data(request):
    """Get accumulated wizard data from session."""
    return request.session.get('onboarding_data', {})


def _save_wizard_data(request, step_data):
    """Merge step data into session."""
    data = _get_wizard_data(request)
    data.update(step_data)
    request.session['onboarding_data'] = data


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
        'form': form,
        'step': 1,
        'total_steps': 4,
        'step_title': 'Business Basics',
    })


@login_required
def wizard_step_2(request):
    if not _get_wizard_data(request).get('business_name'):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        form = BusinessGoalsForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_3')
    else:
        form = BusinessGoalsForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_2.html', {
        'form': form,
        'step': 2,
        'total_steps': 4,
        'step_title': 'Goals & Audience',
    })


@login_required
def wizard_step_3(request):
    if not _get_wizard_data(request).get('business_name'):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        form = BusinessDetailsForm(request.POST)
        if form.is_valid():
            _save_wizard_data(request, form.cleaned_data)
            return redirect('onboarding:step_4')
    else:
        form = BusinessDetailsForm(initial=_get_wizard_data(request))

    return render(request, 'onboarding/step_3.html', {
        'form': form,
        'step': 3,
        'total_steps': 4,
        'step_title': 'Budget & Location',
    })


@login_required
def wizard_step_4(request):
    """Review step — show summary, run AI assessment, generate plan."""
    data = _get_wizard_data(request)
    if not data.get('business_name'):
        return redirect('onboarding:step_1')

    if request.method == 'POST':
        # Create profile, run assessment, generate plan
        profile = OnboardingService.create_business_profile(request.user, data)
        assessment = OnboardingService.run_ai_assessment(profile)
        task_plan = OnboardingService.generate_initial_plan(profile)
        OnboardingService.complete_onboarding(request.user)

        # Clear session data
        request.session.pop('onboarding_data', None)

        return redirect('onboarding:complete')

    # Parse goals for display
    goals_text = data.get('goals', '')
    goals_list = [g.strip() for g in goals_text.split('\n') if g.strip()]

    return render(request, 'onboarding/step_4.html', {
        'data': data,
        'goals_list': goals_list,
        'step': 4,
        'total_steps': 4,
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
