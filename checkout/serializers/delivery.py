import functools
from decimal import Decimal
from payments.calculations.delivery_options import calculate_delivery_options_prices
from typing import Dict, List, Union

from rest_framework import serializers

from carts.models import Cart, CartItem
from core.calculators.order_calculator import OrderCalculatorMixin
from delivery_options.models import DeliveryOption
from products.models import Product


class CheckoutDeliveryItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name")


class CheckoutDeliveryItemDeliveryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryOption
        fields = ("id", "name")


class CheckoutDeliveryItemSerializer(serializers.ModelSerializer):
    product = CheckoutDeliveryItemProductSerializer()
    delivery_option = CheckoutDeliveryItemDeliveryOptionSerializer()
    delivery_options = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        depth = 2
        fields = (
            "id",
            "product",
            "delivery_option",
            "delivery_options",
        )

    def get_delivery_options(
        self, obj: CartItem
    ) -> List[Dict[str, Union[int, Decimal]]]:
        request = self.context.get("request")

        return calculate_delivery_options_prices(request.region, obj)


class CheckoutDeliverySerializer(OrderCalculatorMixin, serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    delivery_fee_net = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            "delivery_address",
            "delivery_fee_net",
            "earliest_delivery_date",
            "items",
        )

    @functools.lru_cache(maxsize=None)
    def _cart_items(self, obj):
        return obj.items.all()

    def get_items(self, obj):
        items = obj.items.order_by("created_at").all()
        return CheckoutDeliveryItemSerializer(
            items, many=True, context=self.context
        ).data

    def get_delivery_fee_net(self, obj):
        return sum([cart_item.delivery_fee_net for cart_item in self._cart_items(obj)])
