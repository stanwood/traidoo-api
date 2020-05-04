from rest_framework import permissions


class IsCronOrTask(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get('HTTP_X_APPENGINE_CRON') or request.META.get('HTTP_X_APPENGINE_QUEUENAME'):
            return True
        return False
