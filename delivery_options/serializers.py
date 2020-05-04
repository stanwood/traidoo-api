from rest_framework import serializers

from .models import DeliveryOption


class DeliveryOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryOption
        fields = ("id", "name")
        read_only_fields = ("id", )
