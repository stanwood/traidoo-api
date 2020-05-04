from rest_framework import permissions


class IsCron(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get('HTTP_X_APPENGINE_CRON'):
            return True
        return False
