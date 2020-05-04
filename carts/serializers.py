import datetime

import pytz
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from carts.models import Cart, CartItem
from products.models import Product

from .utils import validate_earliest_delivery_date


class CartPostSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=0)


class CartDeliveryDatePostSerializer(serializers.Serializer):
    date = serializers.DateField()

    def validate_date(self, value):
        return validate_earliest_delivery_date(value)


class CartDeliveryAddressPostSerializer(serializers.Serializer):
    delivery_address = serializers.IntegerField()


class CartItemDeliveryOptionPostSerializer(serializers.Serializer):
    delivery_option = serializers.IntegerField()
