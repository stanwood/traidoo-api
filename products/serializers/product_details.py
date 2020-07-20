import functools
from decimal import Decimal

from rest_framework import serializers
from taggit_serializer.serializers import TaggitSerializer

from categories.serializers import CategorySerializer
from common.serializers import RegionSerializer
from common.utils import get_region
from containers.serializers import ContainerSerializer
from core.payments.transport_insurance import calculate_transport_insurance_rate
from core.serializers.image_fallback_mixin import ImageFallbackMixin
from core.serializers.regions import CustomRegionsSerializerField
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

    def _transport_insurance(self, obj: Product):
        return functools.reduce(
            lambda prev, next: prev * next,
            [obj.price, obj.amount, calculate_transport_insurance_rate(obj.price)],
        )

    # fixme: Duplicated calculation of delivery, to refactor
    def get_delivery(self, obj):
        request = self.context.get("request")
        region = get_region(request)

        # Pickup
        pickup = Decimal("0.0")

        # Seller delivery
        seller_net = obj.delivery_charge
        seller_vat_rate = obj.vat
        seller_gross = (seller_net * seller_vat_rate / Decimal("100")).quantize(
            Decimal(".01"), "ROUND_HALF_UP"
        )

        options = {"seller": seller_gross, "pickup": pickup}

        region_settings = get_setting(region.id)
        if region_settings.central_logistics_company:
            # Logistics company delivery
            logistics_net = self._transport_insurance(obj)

            container_delivery_fee = obj.container_type.delivery_fee
            if container_delivery_fee:
                logistics_net += container_delivery_fee

            logistics_vat_rate = region_settings.mc_swiss_delivery_fee_vat
            logistics_gross = (
                logistics_net * logistics_vat_rate / Decimal("100")
            ).quantize(Decimal(".01"), "ROUND_HALF_UP")

            options["logistics"] = logistics_gross

        return options
