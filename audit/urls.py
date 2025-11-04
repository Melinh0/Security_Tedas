from django.urls import path
from .views import RegistroListView

urlpatterns = [
    path('registros/', RegistroListView.as_view(), name='registro-list'),
]