import functools
import json
from decimal import Decimal
from json import JSONDecodeError

import six
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from taggit.models import Tag
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField

from categories.serializers import CategorySerializer
from common.serializers import RegionSerializer
from common.utils import get_region
from containers.serializers import ContainerSerializer
from core.payments.transport_insurance import calculate_transport_insurance_rate
from core.serializers.blankable_decimal_field import BlankableDecimalField
from core.serializers.image_fallback_mixin import ImageFallbackMixin
from core.serializers.regions import CustomRegionsSerializerField
from delivery_options.models import DeliveryOption
from delivery_options.serializers import DeliveryOptionSerializer
from products.models import Product
from settings.models import get_setting
from users.serializers import AnonymousUserSerializer


class BaseProductSerializer(serializers.Serializer):
    delivery_options = serializers.SerializerMethodField()

    def get_delivery_options(self, obj: Product):
        request = self.context.get("request")
        region = get_region(request)
        region_settings = region.settings.first()

        if region_settings.central_logistics_company:
            delivery_options = obj.delivery_options
        else:
            delivery_options = obj.delivery_options.exclude(
                id=DeliveryOption.CENTRAL_LOGISTICS
            )

        serialized_delivery_options = DeliveryOptionSerializer(
            delivery_options.order_by("id"), many=True
        )
        return serialized_delivery_options.data


class CustomTagListSerializerField(TagListSerializerField):

    # FIXME: https://github.com/glemmaPaul/django-taggit-serializer/issues/34

    def to_internal_value(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except JSONDecodeError:
                raise ValidationError("Value is not parsable")
        if not isinstance(value, list):
            raise ValidationError("Value is not a list")

        try:
            value = [int(tag_id) for tag_id in value]
        except ValueError:
            raise ValidationError("Tag ids must be integers")
        new_values = []
        for tag_id in value:
            if not isinstance(tag_id, six.integer_types):
                raise ValidationError("Only integers are allowed")

            try:
                tag = Tag.objects.get(id=tag_id)
            except Tag.DoesNotExist:
                raise ValidationError(f"Tag with ID {tag_id} does not exist")
            else:
                new_values.append(tag.name)

        return new_values

    def to_representation(self, value):
        if type(value) is not list:
            return [
                {"id": tag.id, "name": tag.name, "slug": tag.slug}
                for tag in value.all()
            ]
        return value


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


class ProductSnapshotSerializer(
    TaggitSerializer, ImageFallbackMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()
    tags = CustomTagListSerializerField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = "__all__"
        depth = 3
        ordering = ["-created"]


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


class SimpleProductSerializer(ImageFallbackMixin, serializers.ModelSerializer):

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
