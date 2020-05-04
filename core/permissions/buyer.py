from rest_framework import permissions


class IsBuyerUser(permissions.BasePermission):
    """
    Allows access only to buyers.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_buyer:
            return True
        return False


class IsBuyerOrAdminUser(permissions.BasePermission):
    """
    Allows access only for admins or buyers.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and (
            request.user.is_buyer or request.user.is_admin
        ):
            return True
        return False
