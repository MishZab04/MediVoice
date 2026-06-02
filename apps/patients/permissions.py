from rest_framework import permissions
from apps.authentication.models import UserRole


class IsPatientOwner(permissions.BasePermission):
    """
    Object-level permission: health workers can only access their own patients.
    Admins can access any patient.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        return obj.health_worker == request.user
