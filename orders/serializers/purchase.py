from rest_framework import serializers

from documents.models import Document
from documents.utils.document_types import get_buyer_document_types
from orders.models import Order

from .document import DocumentSerializer


class PurchaseSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "created_at", "total_price", "documents")

    def get_documents(self, obj):
        return DocumentSerializer(
            Document.objects.filter(
                order=obj, document_type__in=get_buyer_document_types(obj.buyer)
            ).values("id", "document_type"),
            many=True,
        ).data
