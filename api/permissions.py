#api/permissions.py
from rest_framework.permissions import BasePermission

class RoleRequired(BasePermission):
    def has_permission(self, request, view):
        required_roles = getattr(view, 'required_roles', [])
        
        # Admin tem acesso a tudo
        if request.user.role == 'admin':
            return True
        
        # Verifica se o usuário tem uma das funções necessárias
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        
        return request.user.role in required_roles