import datetime
from distutils import util

from django.db.models import BooleanField, Case, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from common.utils import get_region
from core.permissions.get_permissions import GetPermissionsMixin
from core.permissions.owner import IsOwnerOrAdmin
from core.permissions.seller import IsSellerOrAdminUser
from products.models import Product
from products.serializers import (
    AnonymousProductSerializer,
    ProductDetailsSerializer,
    ProductSerializer,
)


class ProductViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    permission_classes_by_action = {
        "create": [IsSellerOrAdminUser],
        "update": [IsSellerOrAdminUser],
        "partial_update": [IsSellerOrAdminUser],
        "destroy": [IsOwnerOrAdmin],
        "default": [AllowAny],
    }

    search_fields = (
        "id",
        "name",
        "description",
        "category__name",
        "category__parent__name",
        "seller__first_name",
        "seller__last_name",
        "seller__company_name",
        "amount",
        "price",
        "ean8",
        "ean13",
        "sellers_product_identifier",
    )

    filterset_fields = search_fields + (
        "is_organic",
        "is_vegan",
        "is_gluten_free",
        "seller__id",
    )

    ordering_fields = filterset_fields + ("category__id",)

    def get_queryset(self):
        region = get_region(self.request)

        utcnow = datetime.datetime.utcnow().date()
        params = self.request.query_params

        queryset = (
            Product.objects.select_related(
                "category", "seller", "container_type", "category__parent", "region"
            )
            .prefetch_related("items", "items__product", "tags", "delivery_options")
            .filter(Q(region_id=region.id) | Q(regions__in=[region.id]))
            .annotate(
                items_available=Coalesce(
                    Sum(
                        "items__quantity",
                        filter=Q(items__latest_delivery_date__gt=utcnow),
                    ),
                    0,
                )
            )
            .annotate(
                is_available=Case(
                    When(items_available__gt=0, then=Value(1)),
                    default=Value(0),
                    output_field=BooleanField(),
                )
            )
        )

        if "is_available" in params:
            if util.strtobool(params["is_available"]):
                queryset = queryset.filter(items_available__gt=0)
            else:
                queryset = queryset.filter(items_available=0)

        if "category__id" in params:
            # TODO: how many subcategories do we want to support?
            queryset = queryset.filter(
                Q(category__id=params["category__id"])
                | Q(category__parent__id=params["category__id"])
                | Q(category__parent__parent__id=params["category__id"])
                | Q(category__parent__parent__parent__id=params["category__id"])
            )

        # TODO: return error if anonymous and my=

        if self.request.user.is_authenticated and params.get("my", None) is not None:
            queryset = queryset.filter(seller=self.request.user)

        return queryset.order_by(
            Case(
                When(region_id=region.id, then=0),
                default=1,
                output_field=IntegerField(),
            )
        )

    def get_serializer_class(self):
        if self.request.user.is_authenticated and self.request.user.approved:
            if self.action == "retrieve":
                return ProductDetailsSerializer
            return ProductSerializer
        return AnonymousProductSerializer

    def perform_create(self, serializer):
        serializer.validated_data["region_id"] = get_region(self.request).id
        serializer.save()
