from django.contrib.auth import get_user_model
from rest_framework import serializers

from containers.models import Container
from delivery_addresses.models import DeliveryAddress
from orders.models import Order, OrderItem
from products.models import Product

from .models import Job

User = get_user_model()


class JobUserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("company_name", "zip", "city", "street", "first_name", "last_name")


class JobContainererializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = ("size_class",)


class JobProductSerializer(serializers.ModelSerializer):
    seller = JobUserAddressSerializer()
    container_type = JobContainererializer()

    class Meta:
        model = Product
        fields = ("name", "seller", "container_type", "amount", "unit")


class JobDeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = ("company_name", "zip", "city", "street")


class JobOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("earliest_delivery_date",)


class JobOrderItemSerializer(serializers.ModelSerializer):
    product = JobProductSerializer()
    delivery_address = JobDeliveryAddressSerializer()
    order = JobOrderSerializer()

    class Meta:
        model = OrderItem
        fields = (
            "delivery_address",
            "latest_delivery_date",
            "product",
            "quantity",
            "delivery_date",
            "delivery_fee",
            "order",
        )


class JobSerializer(serializers.ModelSerializer):
    order_items = JobOrderItemSerializer(many=True)
    detour = serializers.IntegerField()

    class Meta:
        model = Job
        fields = "__all__"
