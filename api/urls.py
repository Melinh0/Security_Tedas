from django.urls import path
from .views import (
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    UserListView,
    UserDetailView,
    AdminListView,
    AdminDetailView,
    RegistroListView,
    PacienteListView, 
    PacienteDetailView, 
    FatiaTomografiaListView, 
    FatiaTomografiaDetailView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    path('profissional-saude/', UserListView.as_view(), name='user-list'),
    path('profissional-saude/<pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profissional-saude/me/', UserDetailView.as_view(), name='user-me'),
    
    path('admins/', AdminListView.as_view(), name='admin-list'),
    path('admins/<pk>/', AdminDetailView.as_view(), name='admin-detail'),
    path('admins/me/', AdminDetailView.as_view(), name='admin-me'),
    
    path('registros/', RegistroListView.as_view(), name='registro-list'),
    
    path('pacientes/', PacienteListView.as_view(), name='paciente-list'),
    path('pacientes/<int:pk>/', PacienteDetailView.as_view(), name='paciente-detail'),
    path('fatias-tomografia/', FatiaTomografiaListView.as_view(), name='fatiatomografia-list'),
    path('fatias-tomografia/<int:pk>/', FatiaTomografiaDetailView.as_view(), name='fatiatomografia-detail'),
]