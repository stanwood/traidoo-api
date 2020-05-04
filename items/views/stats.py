from django.utils import timezone
from rest_framework import views
from rest_framework.response import Response

from carts.models import CartItem
from core.permissions.seller import IsSellerUser
from orders.models import Order, OrderItem

from ..models import Item
from ..serializers import ItemSerializer


class ItemsStatsView(views.APIView):
    permission_classes = (IsSellerUser,)

    # TODO: FE should make 4 requests instead of this one

    def get(self, request, format=None):
        return Response(
            {
                'available': ItemSerializer(
                    Item.objects.filter(
                        product__seller_id=self.request.user.id,
                        quantity__gt=0,
                        latest_delivery_date__gt=timezone.now(),
                    ).order_by('latest_delivery_date', 'product__name')[0:5],
                    many=True,
                ).data,
                'unsold': ItemSerializer(
                    Item.objects.filter(
                        product__seller_id=self.request.user.id,
                        quantity__gt=0,
                        latest_delivery_date__lte=timezone.now(),
                    ).order_by('latest_delivery_date', 'product__name')[0:5],
                    many=True,
                ).data,
                'cart': ItemSerializer(
                    CartItem.objects.filter(
                        product__seller_id=self.request.user.id
                    ).order_by('latest_delivery_date', 'product__name')[0:5],
                    many=True,
                ).data,
                'paid': ItemSerializer(
                    OrderItem.objects.filter(
                        product__seller_id=self.request.user.id,
                        order__status=Order.STATUSES.get_value('paid'),
                    ).order_by('latest_delivery_date', 'product__name')[0:5],
                    many=True,
                ).data,
            }
        )
