from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


def signup_view(request):
    # TODO: Sprint 3 — signup form + UserProfile creation
    return HttpResponse('Signup — coming soon')


@login_required
def dashboard_view(request):
    # TODO: Sprint 4 — dashboard with today's tasks + progress
    return HttpResponse('Dashboard — coming soon')


@login_required
def profile_view(request):
    # TODO: Sprint 3 — edit notification preferences
    return HttpResponse('Profile — coming soon')
