from rest_framework import serializers

from delivery_addresses.models import DeliveryAddress


class DeliveryAddressSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = DeliveryAddress
        fields = ("id", "company_name", "street", "zip", "city")
