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
    def post(self, request, order_id, format=None):
        order_items = OrderItem.objects.filter(
            order_id=order_id, product__third_party_delivery=True
        )

        jobs = {}

        for order_item in order_items:
            job = jobs.get(order_item.product.seller.id)
            if not job:
                job = Job.objects.create()

            order_item.job = job
            order_item.save()

            if not jobs.get(order_item.product.seller.id):
                jobs[order_item.product.seller.id] = job

        for user in User.objects.filter(
            is_email_verified=True, is_active=True, routes__isnull=False
        ).distinct():
            for _, job in jobs.items():
                for route in user.routes.all():
                    logger.debug(
                        f"CalculateDetour: user: {user.id}, job: {job.id}, route {route.id}"
                    )

                    order_item = job.order_items.first()

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
