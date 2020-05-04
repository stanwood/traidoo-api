from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from core.permissions.get_permissions import GetPermissionsMixin
from core.permissions.owner import IsOwnerOrAdmin
from core.permissions.seller import IsSellerOrAdminUser
from items.models import Item
from items.serializers import ItemSerializer


class ItemViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    OWNER_FIELD = "product.seller"

    serializer_class = ItemSerializer

    permission_classes_by_action = {
        "create": [IsSellerOrAdminUser],
        "update": [IsSellerOrAdminUser, IsOwnerOrAdmin],
        "partial_update": [IsSellerOrAdminUser, IsOwnerOrAdmin],
        "destroy": [IsSellerOrAdminUser, IsOwnerOrAdmin],
        "default": [IsAuthenticated],
    }

    search_fields = (
        "created_at",
        "updated_at",
        "latest_delivery_date",
        "product__name",
        "product__description",
        "product__image_url",
        "product__category__name",
        "product__category__parent__name",
    )

    ordering_fields = search_fields + (
        "id",
        "quantity",
        "valid_from",
        "product__is_organic",
        "product__is_vegan",
        "product__is_gluten_free",
        "product__id",
        "product__created_at",
        "product__updated_at",
        "product__category__id",
        "product__amount",
        "product__unit",
        "product__price",
        "product__vat",
        "product__delivery_charge",
        "product__ean8",
        "product__ean13",
        "product__sellers_product_identifier",
    )

    # TODO: what's the better way?
    filterset_fields = {
        "id": ["exact"],
        "quantity": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "valid_from": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "product__is_organic": ["exact"],
        "product__is_vegan": ["exact"],
        "product__is_gluten_free": ["exact"],
        "product__id": ["exact"],
        "product__created_at": ["exact"],
        "product__updated_at": ["exact"],
        "product__category__id": ["exact"],
        "product__amount": ["exact"],
        "product__unit": ["exact"],
        "product__price": ["exact"],
        "product__vat": ["exact"],
        "product__delivery_charge": ["exact"],
        "product__ean8": ["exact"],
        "product__ean13": ["exact"],
        "product__sellers_product_identifier": ["exact"],
        "created_at": ["exact"],
        "updated_at": ["exact"],
        "latest_delivery_date": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "product__name": ["exact"],
        "product__description": ["exact"],
        "product__image_url": ["exact"],
        "product__category__name": ["exact"],
        "product__category__parent__name": ["exact"],
    }

    def get_queryset(self):
        queryset = Item.objects.select_related("product")

        # TODO: return error if anonymous and my=

        if (
            self.request.user.is_authenticated
            and self.request.query_params.get("my", None) is not None
        ):
            queryset = queryset.filter(product__seller=self.request.user)

        return queryset


class ProductsItemViewSet(ItemViewSet):
    def get_queryset(self):
        return Item.objects.select_related("product").filter(
            product=self.kwargs["product_pk"]
        )
