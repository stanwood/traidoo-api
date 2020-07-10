from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.db.models import F, IntegerField, Q, Sum
from django.db.models.functions import Cast
from rest_framework import serializers

from documents.models import Document
from orders.models import Order

from .document import DocumentSerializer

User = get_user_model()


class SaleBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "company_name")


class SaleSerializer(serializers.ModelSerializer):
    buyer = SaleBuyerSerializer()
    documents = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "created_at", "total_price", "documents", "buyer")

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
