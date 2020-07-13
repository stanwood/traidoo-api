from django.contrib import admin
from django.contrib.admin import ModelAdmin

from items.models import Item


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    ordering = ("latest_delivery_date",)
    list_display = (
        "id",
        "product",
        "latest_delivery_date",
        "quantity",
    )
    list_display_links = [
        "product",
    ]
