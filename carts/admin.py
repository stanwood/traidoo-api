from django.contrib import admin
from reversion.admin import VersionAdmin

from carts.models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(VersionAdmin):
    ordering = ('-created_at', )
    list_display = (
        'id',
        'user',
    )
    list_display_links = [
        'user',
    ]


@admin.register(CartItem)
class CartItemAdmin(VersionAdmin):
    ordering = ('-created_at', )
    list_display = (
        'id',
        'cart',
        'product',
        'latest_delivery_date',
        'quantity',
    )
    list_display_links = [
        'cart',
        'product',
    ]
