from rest_framework import serializers

from containers.models import Container
from core.serializers.image_fallback_mixin import ImageFallbackMixin


class ContainerSerializer(ImageFallbackMixin, serializers.ModelSerializer):
    deposit = serializers.FloatField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Container
        fields = (
            "id",
            "deposit",
            "image",
            "size_class",
            "standard",
            "volume",
            "delivery_fee",
            "image_url"
        )
        read_only_fields = ("id", )
