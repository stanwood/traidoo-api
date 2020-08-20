from admirarchy.utils import HierarchicalModelAdmin
from django import forms
from django.contrib import admin
from django.forms.widgets import Select

from categories.models import Category, CategoryIcon
from common.admin import BaseRegionalAdminMixin


class CustomSelect(Select):
    option_template_name = "categories/select_option.html"


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj


@admin.register(Category)
class CategoryAdmin(BaseRegionalAdminMixin, HierarchicalModelAdmin):
    hierarchy = True
    ordering = ("name",)
    list_display = ("name", "icon", "ordering", "default_vat", "parent")
    list_display_links = ["name"]
    autocomplete_fields = ["parent"]
    search_fields = ["name"]

    class Media:
        js = ("categories/select.js",)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "icon":
            return CategoryChoiceField(
                queryset=CategoryIcon.objects.all(), widget=CustomSelect
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
