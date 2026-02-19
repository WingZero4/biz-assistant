from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def task_list_view(request):
    # TODO: Sprint 4 — task list with filters
    return HttpResponse('Tasks — coming soon')


@login_required
def task_detail_view(request, pk):
    # TODO: Sprint 4 — single task detail
    return HttpResponse(f'Task {pk} — coming soon')


@login_required
def mark_done_view(request, pk):
    # TODO: Sprint 4 — mark task done
    return HttpResponse(f'Task {pk} done — coming soon')


@login_required
def mark_skip_view(request, pk):
    # TODO: Sprint 4 — skip task
    return HttpResponse(f'Task {pk} skipped — coming soon')
