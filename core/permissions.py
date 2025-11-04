from rest_framework.permissions import BasePermission

class RoleRequired(BasePermission):
    def has_permission(self, request, view):
        required_roles = getattr(view, 'required_roles', [])
        
        if request.user.role == 'admin':
            return True
        
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        
        return request.user.role in required_roles