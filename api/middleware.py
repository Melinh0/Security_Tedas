from django.conf import settings

from .audit import log_event


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith('/api/'):
            return response
        if not settings.AUDIT_LOG_ENABLED:
            return response

        status = response.status_code
        if status in (401, 403):
            action = 'ACCESS_DENIED'
        elif status == 429:
            action = 'ACCESS_THROTTLED'
        else:
            action = 'ACCESS'

        user = getattr(request, 'user', None)
        if user is not None and not user.is_authenticated:
            user = None

        log_event(action, user=user, request=request, status_code=status)
        return response
