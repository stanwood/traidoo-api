from django.contrib import admin
from reversion.admin import VersionAdmin

from categories.models import Category


@admin.register(Category)
class CategoryAdmin(VersionAdmin):
    ordering = ('name', )
    list_display = (
        'id',
        'name',
        'icon',
        'ordering',
        'default_vat',
        'parent',
    )
    list_display_links = [
        'parent',
    ]
