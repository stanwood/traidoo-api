from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from overlays.models import Overlay, OverlayButton


class OverlayButtonInlineItem(BaseRegionalAdminMixin, admin.TabularInline):
    model = OverlayButton
    extra = 1


@admin.register(Overlay)
class OverlayAdmin(BaseRegionalAdminMixin, VersionAdmin):
    list_display = ("id", "overlay_type")
    inlines = (OverlayButtonInlineItem,)

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super(OverlayAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            read_only_fields += ("region")
        return read_only_fields
