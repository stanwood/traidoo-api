from loguru import logger
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions.get_permissions import GetPermissionsMixin
from core.permissions.owner import IsOwner
from core.tasks.mixin import TasksMixin

from .models import Route
from .serializers import RouteSerializer


class RoutesViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    OWNER_FIELD = 'user'

    serializer_class = RouteSerializer

    permission_classes_by_action = {
        'update': [IsOwner],
        'partial_update': [IsOwner],
        'destroy': [IsOwner],
        'default': [IsAuthenticated],
    }

    def get_queryset(self):
        return Route.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        route = serializer.save()
        route.calculate_route_length()
        route.save()

        TasksMixin().send_task(
            f'/detours/create/{route.id}',
            queue_name='routes',
            http_method='POST',
            schedule_time=60,
        )

    def perform_update(self, serializer):
        previous_origin = serializer.instance.origin
        previous_destination = serializer.instance.destination
        previous_waypoints = serializer.instance.waypoints

        route = serializer.save()

        if (
            previous_origin != route.origin
            or previous_destination != route.destination
            or set(previous_waypoints) != set(route.waypoints)
        ):
            route.calculate_route_length()
            route.save()

            TasksMixin().send_task(
                f'/detours/update/{route.id}',
                queue_name='routes',
                http_method='POST',
                schedule_time=60,
            )
