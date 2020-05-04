from rest_framework import serializers

from .models import Route


class RouteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    length = serializers.IntegerField(read_only=True)

    class Meta:
        model = Route
        fields = '__all__'

    def validate_frequency(self, value):
        if not value:
            raise serializers.ValidationError(
                'This field is required.', code='required'
            )
        return value
