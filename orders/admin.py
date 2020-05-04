from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from orders.models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(BaseRegionalAdminMixin, VersionAdmin):
    ordering = ("-earliest_delivery_date",)
    list_display = (
        "id",
        "buyer",
        "status",
        "total_price",
        "earliest_delivery_date",
        "created_at",
    )
    list_display_links = ["buyer"]
    list_filter = ["status"]


@admin.register(OrderItem)
class OrderItemAdmin(VersionAdmin):
    ordering = ("-latest_delivery_date",)
    list_display = (
        "id",
        "product",
        "order",
        "latest_delivery_date",
        "delivery_address",
        "quantity",
        "delivery_option",
    )
    list_display_links = ["product", "order", "delivery_address", "delivery_option"]
