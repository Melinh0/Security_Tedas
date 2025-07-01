#api/urls.py
from django.urls import path
from .views import (
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    UserListView,
    UserDetailView,
    AdminListView,
    AdminDetailView,
    LogListView,
    FileUploadView,
    FileListView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/me/', UserDetailView.as_view(), name='user-me'),
    
    path('admins/', AdminListView.as_view(), name='admin-list'),
    path('admins/<pk>/', AdminDetailView.as_view(), name='admin-detail'),
    path('admins/me/', AdminDetailView.as_view(), name='admin-me'),
    
    path('logs/', LogListView.as_view(), name='log-list'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('users/me/upload/', FileUploadView.as_view(), name='file-upload'),
]