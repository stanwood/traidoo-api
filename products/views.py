import datetime
from distutils import util

from django.db.models import (
    BooleanField,
    Case,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny

from core.permissions.get_permissions import GetPermissionsMixin
from core.permissions.owner import IsOwnerOrAdmin
from core.permissions.seller import IsSellerOrAdminUser
from items.models import Item
from products.models import Product
from products.serializers import (
    AnonymousProductSerializer,
    ProductDetailsSerializer,
    ProductSerializer,
)
from products.serializers.product_list import (
    ListProductAnonymousSerializer,
    ListProductSerializer,
)


class ProductViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes_by_action = {
        "create": [IsSellerOrAdminUser],
        "update": [IsOwnerOrAdmin],
        "partial_update": [IsOwnerOrAdmin],
        "destroy": [IsOwnerOrAdmin],
        "default": [AllowAny],
    }

    search_fields = ("name",)

    filterset_fields = search_fields + (
        "is_organic",
        "is_vegan",
        "is_gluten_free",
        "seller__id",
    )

    ordering_fields = filterset_fields + ("category__id", "created_at")

    def get_queryset(self):
        utcnow = datetime.datetime.utcnow().date()
        params = self.request.query_params

        subquery_items = (
            Item.objects.filter(product_id=OuterRef("id")).order_by().values("product")
        )
        subquery_quantity = subquery_items.annotate(
            total=Coalesce(
                Sum("quantity", filter=Q(latest_delivery_date__gt=utcnow)), Value(0)
            )
        ).values("total")

        queryset = (
            Product.objects.select_related(
                "category", "seller", "container_type", "category__parent", "region"
            )
            .prefetch_related("items", "items__product", "tags", "delivery_options")
            .filter(
                Q(region_id=self.request.region.id)
                | Q(regions__in=[self.request.region.id])
            )
            .annotate(items_available=Subquery(subquery_quantity))
            .annotate(
                is_available=Case(
                    When(items_available__gt=0, then=Value(1)),
                    default=Value(0),
                    output_field=BooleanField(),
                )
            )
            .distinct()
        )

        if "is_available" in params:
            if util.strtobool(params["is_available"]):
                queryset = queryset.filter(items_available__gt=0)
            else:
                queryset = queryset.filter(
                    Q(items_available=0) | Q(items_available=None)
                )

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
                When(region_id=self.request.region.id, then=0),
                default=1,
                output_field=IntegerField(),
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            if self.request.user.is_authenticated and self.request.user.approved:
                return ListProductSerializer
            return ListProductAnonymousSerializer

        # TODO: Use a separate serializer for product detail and adding/editing a product

        if self.request.user.is_authenticated and self.request.user.approved:
            # FIXME: Why ProductDetailsSerializer is only used to retrieve the data?
            if self.action == "retrieve":
                return ProductDetailsSerializer
            return ProductSerializer
        return AnonymousProductSerializer

    def perform_create(self, serializer):
        serializer.validated_data["region_id"] = self.request.region.id
        serializer.save()
