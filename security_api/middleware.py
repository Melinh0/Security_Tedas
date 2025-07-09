# security_api/middleware.py
class TokenDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'swagger' in request.path:
            print(f"[DEBUG] Token in sessionStorage: {request.session.get('swagger_token', 'NOT FOUND')}")
        return response