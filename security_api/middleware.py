# security_api/middleware.py
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Adicionar headers de segurança
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self' https:"
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        
        # Adicione este header para forçar HTTPS
        if not request.is_secure():
            response['Location'] = request.build_absolute_uri().replace('http://', 'https://')
            response.status_code = 301
            
        return response