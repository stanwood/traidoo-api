from rest_framework import viewsets

from core.permissions.buyer_or_seller import IsBuyerOrSellerUser
from orders.models import Order
from orders.serializers.purchase import PurchaseSerializer


class PurchasesViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [IsBuyerOrSellerUser]
    http_method_names = ["get"]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user,)
