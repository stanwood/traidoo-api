import collections
import itertools

from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.task import IsTask
from routes.models import Route

from loguru import logger


class CalculateRouteLengthView(views.APIView):
    permission_classes = (AllowAny, IsTask)

    def post(self, request, route_id, format=None):
        try:
            route = Route.objects.get(id=route_id)
        except Route.DoesNotExist:
            logger.error(
                f'CalculateRouteLength: route with id {route_id} does not exist.'
            )
        else:
            route.calculate_route_length()
            route.save()
            logger.debug(
                f'CalculateRouteLength: route ({route_id}) length: {route.length}'
            )

        return Response()
