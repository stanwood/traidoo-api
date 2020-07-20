from rest_framework import serializers

from common.serializers import RegionSerializer
from products.models import Product
from products.serializers.product import ProductSerializer


class AnonymousProductSerializer(ProductSerializer):
    image = serializers.ImageField(required=False)
    region_id = serializers.IntegerField(write_only=True, required=False)
    region_ids = serializers.ListField(
        child=serializers.IntegerField(write_only=True),
        write_only=True,
        source="regions",
        required=False,
    )
    region = RegionSerializer(read_only=True)
    regions = RegionSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "id",
            "tags",
            "image_url",
            "image",
            "category",
            "category_id",
            "seller",
            "is_organic",
            "is_vegan",
            "is_gluten_free",
            "is_grazing_animal",
            "is_gmo_free",
            "amount",
            "unit",
            "vat",
            "container_type",
            "container_type_id",
            "container_description",
            "delivery_charge",
            "delivery_options",
            "delivery_options_ids",
            "tags",
            "ean8",
            "ean13",
            "sellers_product_identifier",
            "items_available",
            "is_available",
            "created_at",
            "updated_at",
            "seller_id",
            "delivery_requirements",
            "third_party_delivery",
            "base_unit",
            "item_quantity",
            "region_id",
            "region_ids",
            "region",
            "regions",
        )
        depth = 2
        ordering = ["-created"]
