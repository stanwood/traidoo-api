from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only for admins.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_admin:
            return True
        return False
