from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from overlays.models import Overlay


@admin.register(Overlay)
class OverlayAdmin(BaseRegionalAdminMixin, VersionAdmin):
    list_display = ("id", "overlay_type")

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
