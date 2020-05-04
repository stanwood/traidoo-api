import datetime
import functools
import time
from decimal import Decimal
from typing import Dict, List, Union

import pytz
from django.conf import settings
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import empty

from carts.models import Cart, CartItem
from common.utils import get_region
from core.calculators.value import Value
from core.serializers.timestamp import TimestampField
from delivery_options.models import DeliveryOption
from delivery_options.serializers import DeliveryOptionSerializer
from products.models import Product
from products.serializers import ProductSerializer
from settings.utils import get_settings


class CartItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    product_id = serializers.IntegerField(write_only=True)
    product = ProductSerializer(read_only=True)
    price_gross = serializers.FloatField(read_only=True)
    platform_fee_gross = serializers.FloatField(read_only=True)
    delivery_fee_gross = serializers.FloatField(read_only=True)
    delivery_option = DeliveryOptionSerializer(read_only=True)
    delivery_option_id = serializers.IntegerField(write_only=True)
    delivery_options = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id",
            "created_at",
            "updated_at",
            "product",
            "product_id",
            "quantity",
            "latest_delivery_date",
            "price_gross",
            "platform_fee_gross",
            "delivery_fee_gross",
            "delivery_option",
            "delivery_option_id",
            "delivery_options",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "latest_delivery_date",
            "product",
        )
        depth = 2

    def get_delivery_options(
        self, obj: CartItem
    ) -> List[Dict[str, Union[int, Decimal]]]:
        """
        Get the list of available delivery options for given item in the cart
        along with the prices.
        """
        request = self.context.get("request")
        region = get_region(request)

        options = [
            {"id": DeliveryOption.SELLER, "value": obj.seller_delivery.netto},
            {"id": DeliveryOption.BUYER, "value": Decimal("0.0")},
        ]

        region_settings = region.settings.first()
        if region_settings.central_logistics_company:
            options.append(
                {
                    "id": DeliveryOption.CENTRAL_LOGISTICS,
                    "value": obj.central_logistic_delivery(region).netto,
                }
            )

        return options


class CartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = CartItemSerializer(many=True)
    platform_fee_net = serializers.SerializerMethodField()
    platform_fee_gross = serializers.SerializerMethodField()
    delivery_fee_net = serializers.SerializerMethodField()
    delivery_fee_gross = serializers.SerializerMethodField()
    total_container_deposit = serializers.SerializerMethodField()
    net_total = serializers.SerializerMethodField()
    vat_breakdown = serializers.SerializerMethodField()
    product_total = serializers.SerializerMethodField()
    deposit = serializers.SerializerMethodField()
    vat_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            "id",
            "user",
            "items",
            "total_container_deposit",
            "platform_fee_net",
            "platform_fee_gross",
            "delivery_fee_net",
            "delivery_fee_gross",
            "net_total",
            "vat_breakdown",
            "product_total",
            "deposit",
            "vat_total",
            "earliest_delivery_date",
            "delivery_address",
        )

    @functools.lru_cache(maxsize=None)
    def _cart_items(self, obj):
        return obj.items.order_by("created_at").all()

    def get_total_container_deposit(self, obj):
        return float(
            sum(
                [
                    cart_item.container_deposit_net * cart_item.quantity
                    for cart_item in self._cart_items(obj)
                ]
            )
        )

    def get_platform_fee_net(self, obj):
        return sum([cart_item.platform_fee_net for cart_item in self._cart_items(obj)])

    def get_platform_fee_gross(self, obj):
        return sum(
            [cart_item.platform_fee_gross for cart_item in self._cart_items(obj)]
        )

    def get_delivery_fee_net(self, obj):
        return sum([cart_item.delivery_fee_net for cart_item in self._cart_items(obj)])

    def get_delivery_fee_gross(self, obj):
        return sum(
            [cart_item.delivery_fee_gross for cart_item in self._cart_items(obj)]
        )

    def get_net_total(self, obj):
        return sum(
            [
                obj.price,
                self.get_total_container_deposit(obj),
                self.get_platform_fee_net(obj),
                self.get_delivery_fee_net(obj),
            ]
        )

    def _vat_breakdown(self, obj):
        result = {}
        total = 0.0

        settings = get_settings()

        for cart_item in self._cart_items(obj):
            # Product vat
            key = float(cart_item.price.vat_rate)
            if key in result:
                result[key] = result[key] + cart_item.price.vat
            else:
                result[key] = cart_item.price.vat

            # Logistic vat
            delivery_vat_rate = float(cart_item.delivery_fee_vat_rate)
            if delivery_vat_rate in result:
                result[delivery_vat_rate] = (
                    result[delivery_vat_rate] + cart_item.delivery_fee_vat
                )
            else:
                result[delivery_vat_rate] = cart_item.delivery_fee_vat

            # Platform vat
            platform_fee_vat_rate = float(cart_item.platform_fee_vat_rate)
            if platform_fee_vat_rate in result:
                result[platform_fee_vat_rate] = (
                    result[platform_fee_vat_rate] + cart_item.platform_fee_vat
                )
            else:
                result[platform_fee_vat_rate] = cart_item.platform_fee_vat

        # Deposit vat
        total_container_deposit = self.get_total_container_deposit(obj)
        deposit_vat_rate = float(settings.deposit_vat)

        if deposit_vat_rate in result:
            result[deposit_vat_rate] = result[deposit_vat_rate] + (
                total_container_deposit * deposit_vat_rate
            )
        else:
            result[deposit_vat_rate] = total_container_deposit * deposit_vat_rate

        total = sum(list(result.values()))

        return result, total

    def get_vat_breakdown(self, obj):
        breakdown, _ = self._vat_breakdown(obj)
        return breakdown

    def get_vat_total(self, obj):
        _, total = self._vat_breakdown(obj)
        return total

    def get_product_total(self, obj):
        return sum([cart_item.price.netto for cart_item in self._cart_items(obj)])

    def get_deposit(self, obj):
        values = []

        settings = get_settings()

        for cart_item in self._cart_items(obj):
            values.append(
                {
                    "volume": cart_item.product.container_type.volume,
                    "size_class": cart_item.product.container_type.size_class,
                    "unit": f"1 {cart_item.product.unit}",
                    "deposit_per_unit": f"{cart_item.product.container_type.deposit} / {cart_item.product.unit}",
                    "deposit_total": cart_item.product.container_type.deposit
                    * cart_item.quantity,
                    "vat": settings.deposit_vat,
                    "count": cart_item.quantity,
                }
            )

        return values
