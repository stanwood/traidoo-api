import itertools
from decimal import Decimal
from payments.calculations.delivery_options import calculate_delivery_options_prices
from typing import Dict, List, Union

from rest_framework import serializers

from carts.models import Cart, CartItem
from core.calculators.order_calculator import OrderCalculatorMixin
from core.calculators.utils import round_float
from core.calculators.value import Value
from delivery_options.serializers import DeliveryOptionSerializer
from products.models import Product
from products.serializers import ProductSerializer
from settings.utils import get_settings


class CartProductSerializer(ProductSerializer):
    class Meta:
        model = Product
        depth = 1
        fields = (
            "name",
            "id",
            "amount",
            "unit",
            "price",
            "vat",
        )


class CartItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    product_id = serializers.IntegerField(write_only=True)
    product = CartProductSerializer(read_only=True)
    price_gross = serializers.FloatField(read_only=True)
    price_net = serializers.FloatField(read_only=True)
    platform_fee_gross = serializers.FloatField(read_only=True)
    delivery_fee_gross = serializers.FloatField(read_only=True)
    delivery_option = DeliveryOptionSerializer(read_only=True)
    delivery_option_id = serializers.IntegerField(write_only=True)
    delivery_options = serializers.SerializerMethodField()

    class Meta:
        depth = 0
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
            "price_net",
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
        request = self.context.get("request")

        return calculate_delivery_options_prices(request.region, obj)


class CartSerializer(OrderCalculatorMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    items = CartItemSerializer(many=True)
    platform_fee_net = serializers.SerializerMethodField()
    platform_fee_gross = serializers.SerializerMethodField()
    delivery_fee_net = serializers.SerializerMethodField()
    delivery_fee_gross = serializers.SerializerMethodField()
    total_container_deposit = serializers.SerializerMethodField()
    net_total = serializers.SerializerMethodField()
    gross_total = serializers.SerializerMethodField()
    vat_breakdown = serializers.SerializerMethodField()
    product_total = serializers.SerializerMethodField()
    deposit = serializers.SerializerMethodField()
    vat_total = serializers.SerializerMethodField()

    class Meta:
        depth = 0
        model = Cart
        fields = (
            "id",
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
            "gross_total",
            "earliest_delivery_date",
            "delivery_address",
        )

    def get_total_container_deposit(self, obj):
        return float(
            sum(
                [
                    cart_item.container_deposit_net * cart_item.quantity
                    for cart_item in obj.cart_items
                ]
            )
        )

    def get_platform_fee_net(self, obj):
        return sum([cart_item.platform_fee_net for cart_item in obj.cart_items])

    def get_platform_fee_gross(self, obj):
        return sum([cart_item.platform_fee_gross for cart_item in obj.cart_items])

    def get_delivery_fee_net(self, obj):
        return sum([cart_item.delivery_fee_net for cart_item in obj.cart_items])

    def get_delivery_fee_gross(self, obj):
        return sum([cart_item.delivery_fee_gross for cart_item in obj.cart_items])

    def get_net_total(self, obj):
        return sum(
            [
                obj.price,
                self.get_total_container_deposit(obj),
                self.get_platform_fee_net(obj),
                self.get_delivery_fee_net(obj),
            ]
        )

    def get_gross_total(self, obj):
        return self.get_vat_total(obj) + self.get_net_total(obj)

    def _vat_breakdown(self, obj):
        items_values = []
        for cart_item in obj.cart_items:
            items_values.append(cart_item.price)
            items_values.append(cart_item._delivery_fee())
            items_values.append(cart_item.buyer_platform_fee)
            items_values.append(cart_item.container_deposit)
        items_values = sorted(items_values, key=lambda item: item.vat_rate)
        vat_mounts_by_rates = {}
        for vat_rate, items_for_vat_rate in itertools.groupby(
            items_values, lambda item: item.vat_rate
        ):
            sum_net_value = sum(value.netto for value in items_for_vat_rate)
            total_value = Value(sum_net_value, vat_rate)
            vat_mounts_by_rates[float(vat_rate)] = total_value.vat

        total_vat_amount = sum(list(vat_mounts_by_rates.values()))
        total_vat_amount = round_float(total_vat_amount)

        return vat_mounts_by_rates, total_vat_amount

    def get_vat_breakdown(self, obj):
        breakdown, _ = self._vat_breakdown(obj)
        return breakdown

    def get_vat_total(self, obj):
        _, total = self._vat_breakdown(obj)
        return total

    def get_product_total(self, obj):
        return sum([cart_item.price.netto for cart_item in obj.cart_items])

    def get_deposit(self, obj):
        values = []

        settings = get_settings()

        for cart_item in obj.cart_items:
            values.append(
                {
                    "volume": cart_item.product.container_type.volume,
                    "size_class": cart_item.product.container_type.size_class,
                    "unit": cart_item.product.unit,
                    "deposit_net": cart_item.container_deposit_net,
                    "deposit_total": cart_item.container_deposit_net
                    * cart_item.quantity,
                    "vat": settings.deposit_vat,
                    "count": cart_item.quantity,
                }
            )

        return values
