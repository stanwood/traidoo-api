from django.contrib import admin
from django.contrib.admin import ModelAdmin

from common.admin import BaseRegionalAdminMixin
from overlays.models import Overlay, OverlayButton


class OverlayButtonInlineItem(admin.TabularInline):
    model = OverlayButton
    extra = 1


@admin.register(Overlay)
class OverlayAdmin(BaseRegionalAdminMixin, ModelAdmin):
    list_display = ("id", "overlay_type")
    inlines = (OverlayButtonInlineItem,)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields["region"].initial = request.user.region.id
            form.base_fields["region"].disabled = True
        return form

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_delete_permission(request, obj)
