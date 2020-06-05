from itertools import groupby

from django.db.models import Prefetch, Q
from rest_framework import viewsets
from rest_framework.response import Response

from core.permissions.owner import IsOwner
from documents.jinja2_utils import format_price, get_price_value
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

        def totalSum(item):
            return item["count"] * item["amount"] * item["price"]

        products = [item for item in document.lines if item["category"] == "Produkte"]
        deposits = [item for item in document.lines if item["category"] == "Pfand"]
        platforms = [item for item in document.lines if item["category"] == "Plattform"]
        logistics = [item for item in document.lines if item["category"] == "Logistik"]

        productsPrice = sum([totalSum(product) for product in products])
        depositsPrice = sum([totalSum(deposit) for deposit in deposits])
        platformsPrice = sum([totalSum(platform) for platform in platforms])
        logisticsPrice = sum([totalSum(logistic) for logistic in logistics])

        vat = {}
        totalVat = 0
        document.lines.sort(key=lambda item: item["vat_rate"])
        for key, value in groupby(document.lines, key=lambda item: item["vat_rate"]):
            vatSum = sum([get_price_value(item).vat for item in value])
            vat[int(key)] = format_price(vatSum)
            totalVat += vatSum

        totalNet = productsPrice + depositsPrice + platformsPrice + logisticsPrice

        return Response(
            {
                "id": document.order.id,
                "documentId": document.id,
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
                    "vat": vat,
                    "totalNet": format_price(totalNet),
                    "totalVat": format_price(totalVat),
                    "totalGross": format_price(totalNet + totalVat),
                },
            },
        )
