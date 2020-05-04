from typing import List

from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.decorators.feature import require_feature
from core.permissions.task import IsTask
from orders.models import OrderItem
from routes.models import Route
from routes.utils.route_length import calculate_route_length

from ..models import Detour


class CreateDetoursView(views.APIView):
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
    def post(self, request, route_id, format=None):
        try:
            route = Route.objects.get(pk=route_id)
        except Route.DoesNotExist:
            logger.error(f"Route {route_id} does not exist")
            return Response(status=status.HTTP_404_NOT_FOUND)

        order_items = OrderItem.objects.filter(
            product__third_party_delivery=True,
            job__isnull=False,
            order__processed=False,
        )

        logger.debug(f"Creating detours for {order_items.count()} order items.")

        for order_item in order_items:
            Detour.objects.create(
                route=route,
                job=order_item.job,
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
