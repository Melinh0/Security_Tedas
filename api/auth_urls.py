from django.urls import path
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .audit import log_event


class ScopedTokenRefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'refresh'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        log_event('TOKEN_REFRESH', user=user, request=request, status_code=response.status_code)
        return response


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', ScopedTokenRefreshView.as_view(), name='refresh'),
]
