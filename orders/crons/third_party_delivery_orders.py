from django.conf import settings
from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.cron import IsCron
from core.tasks.mixin import TasksMixin
from orders.models import Order


class ThirdPartyDeliveryOrdersView(TasksMixin, views.APIView):
    permission_classes = (AllowAny, IsCron)

    def get(self, request, format=None):
        if not settings.FEATURES["routes"]:
            logger.warning("Routes feature is not enabled")
            return Response(status=status.HTTP_204_NO_CONTENT)

        orders = Order.objects.filter(processed=False).distinct()

        for order in orders:
            logger.debug(
                f"ThirdPartyDeliveryOrdersView :: sending task for order "
                f"with ID {order.id}"
            )
            self.send_task(
                f"/documents/queue/{order.id}/all",
                queue_name="documents",
                http_method="POST",
                schedule_time=60,
                headers={"Region": order.region.slug},
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
