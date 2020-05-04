from rest_framework import permissions


class CurrentUser(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.pk == user.pk


class CurrentUserOrAdmin(permissions.IsAuthenticated):
    # TODO: can we use IsOwnerOrAdmin?

    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.is_admin or obj.pk == user.pk
