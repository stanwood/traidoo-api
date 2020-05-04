from django.db.models import Prefetch, Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from items.models import Item
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from products.models import Product


class OrderViewSet(viewsets.ModelViewSet):

    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get"]

    search_fields = (
        "id",
        "created_at",
        "updated_at",
        "buyer__id",
        "status",
        "total_price",
        "earliest_delivery_date",
    )

    filterset_fields = {
        "id": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "created_at": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "updated_at": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "buyer__id": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "status": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "total_price": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "earliest_delivery_date": ["exact", "gt", "gte", "lt", "lte", "contains"],
    }

    ordering_fields = search_fields + ("buyer__first_name", "buyer__last_name")

    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Order.objects.select_related("buyer")

        if self.request.user.is_admin:
            queryset = queryset.prefetch_related("items")
        else:
            queryset = queryset.prefetch_related("items").filter(
                buyer=self.request.user
            )

        return queryset
