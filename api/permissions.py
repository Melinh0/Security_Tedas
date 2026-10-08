from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    message = 'Acesso restrito ao perfil admin.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_admin


class IsAdminOrUserRole(BasePermission):
    message = 'Acesso restrito aos perfis admin ou user.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_admin or user.role_plain in ('admin', 'user')


class IsAdminOrReadOnly(BasePermission):
    message = 'Apenas o perfil admin pode modificar recursos.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_admin
