from rest_framework import permissions


class IsSellerUser(permissions.BasePermission):
    """
    Allows access only to sellers.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_seller:
            return True
        return False


class IsSellerOrAdminUser(permissions.BasePermission):
    """
    Allows access only for admins or sellers.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and (
            request.user.is_admin or (request.user.is_seller and request.user.approved)
        ):
            return True
        return False
