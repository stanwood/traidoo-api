from rest_framework import serializers

from orders.models import Order
from users.serializers import AnonymousUserSerializer


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
