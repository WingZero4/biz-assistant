from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def wizard_step_1(request):
    # TODO: Sprint 3 — business basics form
    return HttpResponse('Onboarding Step 1 — coming soon')


@login_required
def wizard_step_2(request):
    # TODO: Sprint 3 — goals + target audience
    return HttpResponse('Onboarding Step 2 — coming soon')


@login_required
def wizard_step_3(request):
    # TODO: Sprint 3 — budget + location
    return HttpResponse('Onboarding Step 3 — coming soon')


@login_required
def wizard_step_4(request):
    # TODO: Sprint 3 — review + AI assessment
    return HttpResponse('Onboarding Step 4 — coming soon')


@login_required
def onboarding_complete(request):
    # TODO: Sprint 3 — success page, plan preview
    return HttpResponse('Onboarding Complete — coming soon')
