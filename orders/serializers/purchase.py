from django.db.models import Q
from rest_framework import serializers

from documents.models import Document
from orders.models import Order

from .document import DocumentSerializer


class PurchaseSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "created_at", "total_price", "documents")

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
