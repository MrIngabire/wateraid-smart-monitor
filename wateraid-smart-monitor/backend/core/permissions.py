from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Only ADMIN role."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role_type == 'ADMIN'


class IsManager(permissions.BasePermission):
    """Only MANAGER role."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role_type == 'MANAGER'


class IsManagerOrAdmin(permissions.BasePermission):
    """MANAGER or ADMIN."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role_type in ['MANAGER', 'ADMIN']
        )


class IsTechnician(permissions.BasePermission):
    """Only TECHNICIAN role."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role_type == 'TECHNICIAN'


class IsTechnicianOrAdmin(permissions.BasePermission):
    """TECHNICIAN or ADMIN — for task creation."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role_type in ['TECHNICIAN', 'ADMIN']
        )


class ReadOnlyOrManager(permissions.BasePermission):
    """Authenticated can read; only Manager/Admin can write."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role_type in ['MANAGER', 'ADMIN']