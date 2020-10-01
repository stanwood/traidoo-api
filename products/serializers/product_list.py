from django.contrib.auth import get_user_model
from rest_framework import serializers

from categories.serializers import CategorySerializer
from common.serializers import RegionSerializer
from core.serializers.image_fallback_mixin import ImageFallbackMixin
from products.models import Product

User = get_user_model()


class ListProductSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "city",
            "company_name",
        )
        read_only_fields = (
            "id",
            "first_name",
            "last_name",
            "city",
            "company_name",
        )


class ListProductAnonymousSerializer(ImageFallbackMixin, serializers.ModelSerializer):
    items_available = serializers.IntegerField()
    category = CategorySerializer()
    region = RegionSerializer()
    seller = ListProductSellerSerializer()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "image",
            "category",
            "seller",
            "region",
            "items_available",
            "amount",
        )
        read_only_fields = (
            "id",
            "name",
            "image",
            "category",
            "seller",
            "region",
            "items_available",
            "amount",
        )
        image_fallback_fields = [
            ("image", "image_url"),
        ]


class ListProductSerializer(ImageFallbackMixin, serializers.ModelSerializer):
    items_available = serializers.IntegerField()
    category = CategorySerializer()
    region = RegionSerializer()
    seller = ListProductSellerSerializer()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "image",
            "category",
            "seller",
            "region",
            "items_available",
            "price",
            "unit",
            "amount",
        )
        read_only_fields = (
            "id",
            "name",
            "image",
            "category",
            "seller",
            "region",
            "items_available",
            "price",
            "unit",
            "amount",
        )
        image_fallback_fields = [
            ("image", "image_url"),
        ]
