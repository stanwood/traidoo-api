from operator import attrgetter

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    DEFAULT_OWNER_FIELD = "seller"

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, "OWNER_FIELD", self.DEFAULT_OWNER_FIELD)

        if not request.user.is_authenticated:
            return False

        try:
            owner = attrgetter(owner_field)(obj)
        except AttributeError:
            return False

        if owner == request.user:
            return True

        return False


class IsOwnerOrAdmin(permissions.BasePermission):  # TODO: inherit from IsOwner
    DEFAULT_OWNER_FIELD = "seller"

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, "OWNER_FIELD", self.DEFAULT_OWNER_FIELD)

        if not request.user.is_authenticated:
            return False

        if request.user.is_admin:
            return True

        try:
            owner = attrgetter(owner_field)(obj)
        except AttributeError:
            return False

        if owner == request.user:
            return True

        return False
