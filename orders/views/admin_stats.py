import datetime

from django.db import models
from django.utils import timezone
from rest_framework import status, views
from rest_framework.response import Response

from core.permissions.admin import IsAdminUser
from orders.models import OrderItem


class AdminStatsHandler(views.APIView):
    permission_classes = (IsAdminUser,)

    def _sold_query(self, start_date, end_date=None):
        stats = OrderItem.objects.filter(
            order__status__in=(1, 2), order__created_at__gte=start_date
        )

        if end_date:
            stats = stats.filter(order__created_at__lte=end_date)

        stats = stats.aggregate(
            stats_price=models.Sum(
                models.F('product__price') * models.F('quantity'),
                output_field=models.FloatField(),
            )
        )

        return stats.get('stats_price') or 0

    @staticmethod
    def percentage_change(current_value, previous_value):
        if current_value == previous_value:
            return 0
        try:
            return (
                round((current_value - previous_value) / float(previous_value), 3) * 100
            )
        except ZeroDivisionError:
            return None

    def sold(self, days_in_past):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        current = today - datetime.timedelta(days=days_in_past)

        if days_in_past == 0:
            days_in_past = 1

        previous = current - datetime.timedelta(days=days_in_past)

        current_value = self._sold_query(start_date=current)
        previous_value = self._sold_query(start_date=previous, end_date=current)

        return {
            'value': current_value,
            'change': self.percentage_change(current_value, previous_value),
            'previous': previous_value,
        }

    def get(self, request, format=None):
        return Response({'today': self.sold(0), '7': self.sold(7), '30': self.sold(30)})
