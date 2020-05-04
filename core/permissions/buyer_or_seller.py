from rest_framework import permissions


class IsBuyerOrSellerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and (
            request.user.is_seller or request.user.is_buyer
        ):
            return True
        return False
