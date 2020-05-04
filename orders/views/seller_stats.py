import datetime

from django.db import models
from django.utils import timezone
from rest_framework import status, views
from rest_framework.response import Response

from core.permissions.get_permissions import GetPermissionsMixin
from core.permissions.seller import IsSellerUser
from orders.models import Order, OrderItem


class SellerStatsView(views.APIView):
    permission_classes = (IsSellerUser, )

    def _query(self, seller, status, past_days):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        stats = OrderItem.objects.filter(
            order__status=status,
            product__seller_id=seller.id,
            order__created_at__gte=today - datetime.timedelta(days=past_days)
        ).aggregate(
            stats_price=models.Sum(
                models.F('product__price') * models.F('quantity'),
                output_field=models.FloatField(),
            )
        )

        return stats.get('stats_price') or 0

    def get_stats(self, seller, past_days=0):
        unsold = self._query(seller, 2, past_days)
        sold = self._query(seller, 1, past_days)
        total = unsold + sold

        return {'unsold': unsold, 'sold': sold, 'total': total}

    def get(self, request, format=None):
        return Response({
            'today': self.get_stats(request.user),
            '7': self.get_stats(
                request.user,
                past_days=7,
            ),
            '30': self.get_stats(
                request.user,
                past_days=30,
            ),
            '180': self.get_stats(
                request.user,
                past_days=180,
            ),
        })
