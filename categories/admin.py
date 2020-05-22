from admirarchy.utils import HierarchicalModelAdmin
from django.contrib import admin

from categories.models import Category
from common.admin import BaseRegionalAdminMixin


@admin.register(Category)
class CategoryAdmin(BaseRegionalAdminMixin, HierarchicalModelAdmin):
    hierarchy = True
    ordering = ("name",)
    list_display = ("name", "icon", "ordering", "default_vat", "parent")
    list_display_links = ["name"]
    autocomplete_fields = ["parent"]
    search_fields = ["name"]

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
