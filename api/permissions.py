from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class RoleRequired(BasePermission):
    def has_permission(self, request, view):
        required_roles = getattr(view, 'required_roles', [])
        if not required_roles:
            return True
        
        if request.user.role == 'admin':
            return True
        
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        
        return request.user.role in required_roles