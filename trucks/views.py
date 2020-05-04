from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin
from trucks.models import Truck
from trucks.serializers import TruckSerializer


class TruckViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    pagination_class = None

    filterset_fields = search_fields = ordering_fields = (
        'id',
        'created_at',
        'updated_at',
        'name',
    )

    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'default': [IsAdminUser],
    }
