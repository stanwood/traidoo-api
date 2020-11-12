from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only for admins.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and (
            request.user.is_admin or request.user.is_superuser
        ):
            return True
        return False
