from django.contrib import admin
from reversion.admin import VersionAdmin

from items.models import Item


@admin.register(Item)
class ItemAdmin(VersionAdmin):
    ordering = ('latest_delivery_date', )
    list_display = (
        'id',
        'product',
        'latest_delivery_date',
        'quantity',
    )
    list_display_links = [
        'product',
    ]
