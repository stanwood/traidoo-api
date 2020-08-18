from rest_framework import serializers

from categories.serializers import CategorySerializer
from common.serializers import RegionSerializer
from products.models import Product


class ListProductAnonymousSerializer(serializers.ModelSerializer):
    items_available = serializers.IntegerField()
    category = CategorySerializer()
    region = RegionSerializer()

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
        )
        read_only_fields = (
            "id",
            "name",
            "image",
            "category",
            "seller",
            "region",
            "items_available",
        )


class ListProductSerializer(serializers.ModelSerializer):
    items_available = serializers.IntegerField()
    category = CategorySerializer()
    region = RegionSerializer()

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
        )
