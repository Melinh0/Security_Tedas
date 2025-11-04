from rest_framework import generics, permissions
from .models import Registro
from .serializers import RegistroSerializer
from core.permissions import RoleRequired

class RegistroListView(generics.ListAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return Registro.objects.all().order_by('-timestamp')