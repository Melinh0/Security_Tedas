from django.urls import path
from .views import (
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    UserListView,
    UserDetailView,
    AdminListView,
    AdminDetailView,
)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    path('profissionais/', UserListView.as_view(), name='user-list'),
    path('profissionais/<pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profissionais/me/', UserDetailView.as_view(), name='user-me'),
    
    path('admins/', AdminListView.as_view(), name='admin-list'),
    path('admins/<pk>/', AdminDetailView.as_view(), name='admin-detail'),
    path('admins/me/', AdminDetailView.as_view(), name='admin-me'),
]