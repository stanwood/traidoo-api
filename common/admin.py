from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Region


class BaseRegionalAdminMixin:
    GLOBAL_MODELS = [
        "containers.container",
        "categories.category",
        "items.item",
        "common.region",
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_admin:
            if self.model._meta.label_lower not in self.GLOBAL_MODELS:
                queryset = queryset.filter(region_id=request.user.region_id)
            elif self.model._meta.label_lower == "common.region":
                queryset = queryset.filter(id=request.user.region_id)

        return queryset

    def has_view_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        else:
            return super(BaseRegionalAdminMixin, self).has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.is_admin:
            return (
                obj is None
                or (request.user.region_id == obj.region_id)
                or obj._meta.label_lower in self.GLOBAL_MODELS
            )
        else:
            return super(BaseRegionalAdminMixin, self).has_change_permission(
                request, obj
            )

    def has_delete_permission(self, request, obj=None):
        if request.user.is_admin:
            return (
                obj is None
                or obj._meta.label_lower in self.GLOBAL_MODELS
                or (request.user.region_id == obj.region_id)
            )
        else:
            return super(BaseRegionalAdminMixin, self).has_delete_permission(
                request, obj
            )

    def has_add_permission(self, request):
        if request.user.is_admin:
            return True
        else:
            return super(BaseRegionalAdminMixin, self).has_add_permission(request)

    def save_form(self, request, form, change):
        if request.user.is_admin:
            form.instance.region_id = request.user.region_id

        return super(BaseRegionalAdminMixin, self).save_form(request, form, change)


@admin.register(Region)
class RegionAdmin(BaseRegionalAdminMixin, VersionAdmin):
    list_display = ("id", "name", "slug", "website_slogan")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
