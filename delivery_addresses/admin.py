from django.contrib import admin
from django.contrib.admin import ModelAdmin

from delivery_addresses.models import DeliveryAddress


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(ModelAdmin):
    ordering = ("company_name",)
    list_display = (
        "id",
        "company_name",
        "street",
        "zip",
        "city",
        "user",
    )
    list_display_links = [
        "user",
    ]
