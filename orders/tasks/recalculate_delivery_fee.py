from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.utils import get_region
from core.tasks.mixin import TasksMixin
from orders.models import OrderItem


class RecalculateDeliveryFeeView(TasksMixin, views.APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        region = get_region(request)

        if request.GET.get("token") != "12l31jb31283kjhqweb":
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.send_task(
            f'/order-items/tasks/recalculate-delivery-fee?token={request.GET.get("token")}',
            http_method="POST",
            headers={"Region": region.slug}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        if request.GET.get("token") != "12l31jb31283kjhqweb":
            return Response(status=status.HTTP_403_FORBIDDEN)

        for order_item in OrderItem.objects.all():
            logger.debug(f"Processing order item: {order_item.id}")

            try:
                order_item.save()
            except KeyError:
                logger.debug(
                    f"Empty delivery fee for container, order item: {order_item.id}"
                )

        return Response(status=status.HTTP_204_NO_CONTENT)
