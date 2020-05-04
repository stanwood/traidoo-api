from typing import List

from django.contrib.auth import get_user_model
from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.decorators.feature import require_feature
from core.permissions.task import IsTask
from orders.models import Order, OrderItem
from routes.models import Route
from routes.utils.route_length import calculate_route_length

from ..models import Detour, Job

User = get_user_model()


class CreateJobView(views.APIView):
    permission_classes = (AllowAny, IsTask)

    def _calculate_detour(
        self,
        route_length: int,
        origin: str,
        destination: str,
        waypoints: List[str],
        pickup_address: str,
        delivery_address: str,
    ):
        waypoints = waypoints + [pickup_address, delivery_address]
        length = calculate_route_length(origin, destination, waypoints)

        logger.debug(f"CreateJobView: {length}, {route_length}")

        detour = length - route_length

        if detour < 0:
            detour = -detour

        return detour

    @require_feature("routes")
    def post(self, request, order_item_id, format=None):
        try:
            order_item = OrderItem.objects.get(pk=order_item_id)
        except OrderItem.DoesNotExist:
            logger.error(f"CalculateDetour: order item {order_item_id} does not exist")
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not order_item.product.third_party_delivery:
            logger.error(
                f"CalculateDetour: product ({order_item.product.id}) does not support third party delivery (order item: {order_item.id})"
            )
            return Response()

        job = Job.objects.create(order_item=order_item)

        for user in User.objects.filter(
            is_email_verified=True, is_active=True, routes__isnull=False
        ).distinct():
            logger.debug(f"CalculateDetour: user {user.id}")

            for route in user.routes.all():
                logger.debug(f"CalculateDetour: route {route.id}")

                Detour.objects.create(
                    route=route,
                    job=job,
                    length=self._calculate_detour(
                        route.length,
                        route.origin,
                        route.destination,
                        route.waypoints,
                        order_item.product.seller.address_as_str,
                        order_item.delivery_address_as_str,
                    ),
                )

        return Response()
