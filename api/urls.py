from django.urls import path

from . import views

urlpatterns = [
    path('users/', views.UserAdminListCreateView.as_view(), name='users'),
    path('users/<int:pk>/reveal/', views.UserRevealView.as_view(), name='reveal'),
    path('public/', views.PublicUsersView.as_view(), name='public'),
    path('visible-users/', views.VisibleUsersView.as_view(), name='visible-users'),
    path('me/', views.MeView.as_view(), name='me'),
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-logs'),
    path('upload/avatar/', views.UploadAvatarView.as_view(), name='upload-avatar'),
]
