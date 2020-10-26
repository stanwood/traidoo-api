import functools
from decimal import Decimal

from rest_framework import serializers
from taggit_serializer.serializers import TaggitSerializer

from carts.models import CartItem, Cart
from categories.serializers import CategorySerializer
from common.serializers import RegionSerializer
from common.utils import get_region
from containers.serializers import ContainerSerializer
from core.serializers.image_fallback_mixin import ImageFallbackMixin
from core.serializers.regions import CustomRegionsSerializerField
from delivery_options.models import DeliveryOption
from products.models import Product
from products.serializers.base import BaseProductSerializer
from products.serializers.tag import CustomTagListSerializerField
from settings.models import get_setting
from users.serializers import AnonymousUserSerializer


class ProductDetailsSerializer(
    BaseProductSerializer,
    ImageFallbackMixin,
    serializers.ModelSerializer,
    TaggitSerializer,
):
    items_available = serializers.IntegerField(read_only=True)
    tags = CustomTagListSerializerField(allow_null=True, required=False)
    seller = AnonymousUserSerializer(read_only=True)
    image = serializers.ImageField(required=False)
    delivery = serializers.SerializerMethodField()
    category = CategorySerializer()
    container_type = ContainerSerializer()
    region_id = serializers.IntegerField(write_only=True, required=False)
    regions = CustomRegionsSerializerField(allow_null=True, required=False)
    region = RegionSerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "id",
            "image",
            "category",
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
            "delivery_charge",
            "delivery_options",
            "third_party_delivery",
            "items_available",
            "delivery",
            "region_id",
            "regions",
            "region",
            "ean8",
            "ean13",
            "sellers_product_identifier",
            "tags",
        )
        read_only_fields = ("id",)
        depth = 2
        ordering = ["-created"]

    def get_delivery(self, obj):
        request = self.context.get("request")
        region = get_region(request)

        cart = Cart(user=request.user)
        seller_delivery_cart_item = CartItem(
            product=obj, quantity=1, delivery_option_id=DeliveryOption.SELLER, cart=cart
        )

        options = {
            "seller": seller_delivery_cart_item.seller_delivery_fee.netto,
            "pickup": Decimal("0.0"),
        }

        region_settings = get_setting(region.id)
        if region_settings.central_logistics_company:
            central_logistics_cart_item = CartItem(
                product=obj,
                quantity=1,
                delivery_option_id=DeliveryOption.CENTRAL_LOGISTICS,
                cart=cart,
            )
            options[
                "logistics"
            ] = central_logistics_cart_item.central_logistic_delivery_fee.netto

        return options
