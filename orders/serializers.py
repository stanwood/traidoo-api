import os

from rest_framework import serializers

from delivery_addresses.serializers import DeliveryAddressSerializer
from documents.models import Document
from orders.models import Order, OrderItem
from products.models import Product
from users.serializers import AnonymousUserSerializer


class _ProductSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ("id", "name", "price", "image_url")


class OrderSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    buyer = AnonymousUserSerializer(read_only=True)
    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "buyer",
            "status",
            "total_price",
            "earliest_delivery_date",
            "items",
            "created_at",
            "updated_at",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    product = _ProductSerializer()
    delivery_address = DeliveryAddressSerializer()

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderDocumentSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    filename = serializers.SerializerMethodField()

    def get_filename(self, obj):
        if obj.blob_name:
            return os.path.basename(obj.blob_name)
        else:
            return None

    class Meta:
        model = Document
        fields = ("id", "document_type", "filename")
