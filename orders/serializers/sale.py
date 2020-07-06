from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.db.models import F, IntegerField, Sum
from django.db.models.functions import Cast
from rest_framework import serializers

from documents.models import Document
from documents.utils.document_types import get_seller_document_types
from orders.models import Order

from .document import DocumentSerializer


class SaleSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "created_at", "total_price", "documents")

    def get_total_price(self, obj):
        documents = Document.objects.filter(
            order=obj, document_type__in=get_seller_document_types(),
        )

        return sum(
            sum([item.value.brutto for item in document.calc_items])
            for document in Document.objects.filter(
                order=obj, document_type__in=get_seller_document_types()
            )
        )

    def get_documents(self, obj):
        return DocumentSerializer(
            Document.objects.filter(
                order=obj, document_type__in=get_seller_document_types(),
            ).values("id", "document_type"),
            many=True,
        ).data
