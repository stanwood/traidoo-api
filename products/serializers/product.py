from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from taggit_serializer.serializers import TaggitSerializer

from common.serializers import RegionSerializer
from core.serializers.blankable_decimal_field import BlankableDecimalField
from core.serializers.image_fallback_mixin import ImageFallbackMixin
from core.serializers.regions import CustomRegionsSerializerField
from products.models import Product
from products.serializers.base import BaseProductSerializer
from products.serializers.tag import CustomTagListSerializerField
from users.serializers import AnonymousUserSerializer


class ProductSerializer(
    BaseProductSerializer,
    TaggitSerializer,
    ImageFallbackMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    tags = CustomTagListSerializerField(allow_null=True, required=False)
    items_available = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    seller_id = serializers.IntegerField(write_only=True, required=False)
    category_id = serializers.IntegerField(write_only=True)
    seller = AnonymousUserSerializer(read_only=True)
    container_type_id = serializers.IntegerField(write_only=True)
    delivery_options_ids = serializers.ListField(
        child=serializers.IntegerField(write_only=True),
        write_only=True,
        source="delivery_options",
    )
    image = serializers.ImageField(required=False)
    item_quantity = BlankableDecimalField(
        required=False, allow_null=True, decimal_places=2, max_digits=10
    )
    region_id = serializers.IntegerField(write_only=True, required=False)
    region = RegionSerializer(read_only=True)
    regions = CustomRegionsSerializerField(allow_null=True, required=False)

    def validate(self, data):
        forced_seller_id = data.get("seller_id")
        request_user = self.context["request"].user

        if (
            not request_user.is_seller
            and request_user.is_admin
            and not forced_seller_id
        ):
            raise ValidationError({"seller_id": ["This field is required."]})

        if (
            forced_seller_id
            and forced_seller_id != request_user.id
            and not request_user.is_admin
        ):
            # TODO: forced_seller_id != request_user.id is a quick fix for the frontend issue.
            # The frontend should not send sellerId when a seller wants to add/edit his product.
            raise PermissionDenied({"seller_id": ["Only admin can use this field."]})

        if request_user.is_admin and forced_seller_id:
            data["seller_id"] = forced_seller_id
        else:
            data["seller_id"] = request_user.id

        return data

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "items",
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
            "price",
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
            "region",
            "regions",
        )
        depth = 2
        ordering = ["-created"]
