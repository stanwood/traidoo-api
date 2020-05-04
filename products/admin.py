from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from items.models import Item
from products.models import Product


class ItemsInline(admin.TabularInline):
    model = Item


@admin.register(Product)
class ProductAdmin(BaseRegionalAdminMixin, VersionAdmin):
    list_display = (
        'id',
        'name',
        'is_organic',
        'is_vegan',
        'is_gluten_free',
        'unit',
        'price',
        'region',
        'item_quantity'
    )
    search_fields = (
        'name',
        'category__name',
    )

    list_filter = ('region', )

    inlines = (ItemsInline, )
