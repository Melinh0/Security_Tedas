from django.urls import path
from .views import FatiaTomografiaListView, FatiaTomografiaDetailView

urlpatterns = [
    path('fatias-tomografia/', FatiaTomografiaListView.as_view(), name='fatiatomografia-list'),
    path('fatias-tomografia/<int:pk>/', FatiaTomografiaDetailView.as_view(), name='fatiatomografia-detail'),
]