from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.db.models import F, IntegerField, Q, Sum
from django.db.models.functions import Cast
from rest_framework import serializers

from documents.models import Document
from orders.models import Order

from .document import DocumentSerializer


class SaleSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "created_at", "total_price", "documents")

    def get_total_price(self, obj):
        request = self.context.get("request")

        try:
            return obj.documents.get(
                document_type=Document.TYPES.producer_invoice.value[0],
                seller__user_id=request.user.id,
            ).price_gross
        except Document.DoesNotExist:
            return 0

    def get_documents(self, obj):
        request = self.context.get("request")

        return DocumentSerializer(
            obj.documents.filter(
                Q(seller__user_id=request.user.id) | Q(buyer__user_id=request.user.id),
            )
            .values("id", "document_type")
            .distinct(),
            many=True,
        ).data
