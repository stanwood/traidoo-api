from rest_framework import viewsets

from core.permissions.buyer import IsBuyerUser
from orders.models import Order
from orders.serializers.purchase import PurchaseSerializer


class PurchasesViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [IsBuyerUser]
    http_method_names = ["get"]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user,)
