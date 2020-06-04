from django.db.models import Prefetch, Q
from rest_framework import viewsets
from rest_framework.response import Response

from core.permissions.owner import IsOwner
from documents.jinja2_utils import format_price
from documents.models import Document
from items.models import Item
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from products.models import Product


class OrderViewSet(viewsets.ModelViewSet):
    OWNER_FIELD = "buyer"

    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)
    http_method_names = ["get"]

    filterset_fields = {
        "id": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "created_at": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "updated_at": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "status": ["exact", "gt", "gte", "lt", "lte", "contains"],
        "earliest_delivery_date": ["exact", "gt", "gte", "lt", "lte", "contains"],
    }

    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("buyer")
            .prefetch_related("items")
            .filter(buyer=self.request.user)
        )

        return queryset

    def retrieve(self, request, pk=None):
        document = Document.objects.get(
            document_type=Document.TYPES.order_confirmation_buyer.value[0], order_id=pk
        )

        products = [
            product for product in document.lines if product["category"] == "Produkte"
        ]
        deposits = [
            deposit for deposit in document.lines if deposit["category"] == "Pfand"
        ]
        platforms = [
            platform
            for platform in document.lines
            if platform["category"] == "Plattform"
        ]
        logistics = [
            logistic
            for logistic in document.lines
            if logistic["category"] == "Logistik"
        ]

        productsPrice = sum([product["price"] for product in products])
        depositsPrice = sum([deposit["price"] for deposit in deposits])
        platformsPrice = sum([platform["price"] for platform in platforms])
        logisticsPrice = sum([logistic["price"] for logistic in logistics])

        productsVat = sum([product["vat_rate"] for product in products])
        depositsVat = sum([deposit["vat_rate"] for deposit in deposits])
        platformsVat = sum([platform["vat_rate"] for platform in platforms])
        logisticsVat = sum([logistic["vat_rate"] for logistic in logistics])

        totalNet = productsPrice + depositsPrice + platformsPrice + logisticsPrice
        totalVat = productsVat + depositsVat + platformsVat + logisticsVat

        return Response(
            {
                "id": document.order.id,
                "date": document.order.earliest_delivery_date,
                "status": document.order.status,
                "totalPrice": format_price(document.order.total_price),
                "products": products,
                "deposits": deposits,
                "platforms": platforms,
                "logistics": logistics,
                "summary": {
                    "productsPrice": format_price(productsPrice),
                    "depositsPrice": format_price(depositsPrice),
                    "platformsPrice": format_price(platformsPrice),
                    "logisticsPrice": format_price(logisticsPrice),
                    "productsVat": format_price(productsVat),
                    "depositsVat": format_price(depositsVat),
                    "platformsVat": format_price(platformsVat),
                    "logisticsVat": format_price(logisticsVat),
                    "totalNet": format_price(totalNet),
                    "totalVat": format_price(totalVat),
                    "totalGross": format_price(totalNet + totalVat),
                },
            },
        )
