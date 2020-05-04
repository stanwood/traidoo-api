import datetime

from django.conf import settings
from django.utils import timezone
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.cron import IsCron

from ..models import Cart


class DeleteInactiveCartsView(views.APIView):
    permission_classes = (AllowAny, IsCron)

    @classmethod
    def get_latest_update_time(cls):
        return timezone.now() - datetime.timedelta(minutes=settings.CART_LIFESPAN)

    @classmethod
    def get(cls, request, format=None):
        carts = Cart.objects.filter(updated_at__lt=cls.get_latest_update_time())
        for cart in carts:
            for item in cart.items.all():
                item.release_product_item()
            cart.delete()
        return Response()
