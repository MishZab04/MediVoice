from rest_framework import permissions
from .models import UserRole


class IsAdmin(permissions.BasePermission):
    """Grants access only to users with the Admin role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.ADMIN


class IsHealthWorker(permissions.BasePermission):
    """Grants access to Health Workers and Admins (admin is a superset of health worker)."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (UserRole.HEALTH_WORKER, UserRole.ADMIN)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admins can write; any authenticated user can read."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == UserRole.ADMIN
