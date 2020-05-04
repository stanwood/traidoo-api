from rest_framework import serializers

from trucks.models import Truck


class TruckSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Truck
        fields = '__all__'
