def nav_active(request):
    """Set nav_active based on the current URL path."""
    path = request.path
    if path.startswith('/content'):
        active = 'content'
    elif path.startswith('/chat'):
        active = 'chat'
    elif path.startswith('/analytics'):
        active = 'analytics'
    elif path.startswith('/pulse'):
        active = 'pulse'
    elif path.startswith('/dashboard'):
        active = 'dashboard'
    elif path.startswith('/tasks'):
        active = 'tasks'
    elif path.startswith('/profile'):
        active = 'profile'
    else:
        active = ''
    return {'nav_active': active}
