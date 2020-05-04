from rest_framework import serializers

from orders.models import Order


class PayoutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
    amount = serializers.FloatField(required=True)

    def validate(self, data):
        order_id = data.get("order_id")

        if order_id:
            try:
                Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                raise serializers.ValidationError(
                    f"Order with ID {order_id} does not exist"
                )

        return data
