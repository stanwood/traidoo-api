from django.contrib.auth import get_user_model
from rest_framework import serializers

from containers.serializers import ContainerSerializer
from core.serializers.image_fallback_mixin import ImageFallbackMixin
from products.models import Product

User = get_user_model()


class UserProductSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("password",)


class ProductSnapshotSerializer(ImageFallbackMixin, serializers.ModelSerializer):
    seller = UserProductSnapshotSerializer()
    amount = serializers.FloatField()
    price = serializers.FloatField()
    vat = serializers.FloatField()
    delivery_charge = serializers.FloatField()
    container_type = ContainerSerializer()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = "__all__"
        depth = 2
        ordering = ["-created"]
