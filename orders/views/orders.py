import datetime
import os
from itertools import groupby

import google.cloud.storage
from django.conf import settings
from django.db.models import Prefetch, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions.owner import IsOwner
from documents.jinja2_utils import format_price, get_price_value
from documents.models import Document
from items.models import Item
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from products.models import Product


class BuyerOrderViewSet(viewsets.ModelViewSet):
    OWNER_FIELD = "buyer"

    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)
    http_method_names = ["get"]

    filterset_fields = {
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

    @action(detail=True)
    def download(self, request, pk):
        document = Document.objects.get(
            document_type=Document.TYPES.order_confirmation_buyer.value[0], order_id=pk,
        )

        storage_client = google.cloud.storage.Client.from_service_account_json(
            settings.BASE_DIR.joinpath("service_account.json")
        )

        bucket = storage_client.get_bucket(settings.DEFAULT_BUCKET)
        blob = bucket.blob(document.blob_name)

        filename = os.path.basename(document.blob_name)

        return Response(
            {
                "url": blob.generate_signed_url(
                    datetime.timedelta(minutes=settings.DOCUMENTS_EXPIRATION_TIME),
                    response_disposition=f"attachment; filename={filename}",
                ),
                "filename": filename,
            }
        )
