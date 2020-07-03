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
    readonly_fields = ("region",)
