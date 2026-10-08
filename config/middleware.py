from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        csp = settings.CONTENT_SECURITY_POLICY
        if csp:
            response.headers['Content-Security-Policy'] = csp
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        response.headers.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        if request.is_secure():
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload')
        return response
