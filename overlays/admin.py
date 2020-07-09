from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from overlays.models import Overlay, OverlayButton


class OverlayButtonInlineItem(admin.TabularInline):
    model = OverlayButton
    extra = 1


@admin.register(Overlay)
class OverlayAdmin(BaseRegionalAdminMixin, VersionAdmin):
    list_display = ("id", "overlay_type")
    inlines = (OverlayButtonInlineItem,)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields["region"].initial = request.user.region.id
            form.base_fields["region"].disabled = True
        return form
