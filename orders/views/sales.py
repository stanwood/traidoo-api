from rest_framework import viewsets

from core.permissions.seller import IsSellerUser
from orders.models import Order
from orders.serializers.sale import SaleSerializer


class SalesViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsSellerUser]
    http_method_names = ["get"]

    def get_queryset(self):
        return Order.objects.filter(items__product__seller=self.request.user,)
