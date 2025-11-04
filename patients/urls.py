from django.urls import path
from .views import PacienteListView, PacienteDetailView

urlpatterns = [
    path('pacientes/', PacienteListView.as_view(), name='paciente-list'),
    path('pacientes/<int:pk>/', PacienteDetailView.as_view(), name='paciente-detail'),
]