from django.contrib import admin
from django.contrib.admin import ModelAdmin

from common.admin import BaseRegionalAdminMixin
from containers.models import Container


@admin.register(Container)
class ContainerAdmin(BaseRegionalAdminMixin, ModelAdmin):
    ordering = ("size_class",)
    list_display = (
        "id",
        "size_class",
        "standard",
        "volume",
        "deposit",
        "delivery_fee",
        "image_url",
    )

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
