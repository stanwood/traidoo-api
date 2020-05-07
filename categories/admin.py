from admirarchy.utils import HierarchicalModelAdmin
from django.contrib import admin
from reversion.admin import VersionAdmin

from categories.models import Category
from common.admin import BaseRegionalAdminMixin


@admin.register(Category)
class CategoryAdmin(BaseRegionalAdminMixin, HierarchicalModelAdmin):
    hierarchy = True
    ordering = ("name",)
    list_display = ("name", "icon", "ordering", "default_vat", "parent")
    list_display_links = ["parent"]
    list_display_links = ["name"]
