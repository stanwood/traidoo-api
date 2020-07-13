from django.contrib import admin
from django.contrib.admin import ModelAdmin

from carts.models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "id",
        "user",
    )
    list_display_links = [
        "user",
    ]


@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "id",
        "cart",
        "product",
        "latest_delivery_date",
        "quantity",
    )
    list_display_links = [
        "cart",
        "product",
    ]
