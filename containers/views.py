from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated

from containers.models import Container
from containers.serializers import ContainerSerializer
from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin


class ContainerViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    pagination_class = None

    filterset_fields = search_fields = ordering_fields = (
        'id',
        'created_at',
        'updated_at',
        'size_class',
        'standard',
        'volume',
        'deposit',
        'delivery_fee',
    )

    permission_classes_by_action = {
        'create': [IsAdminUser],
        'update': [IsAdminUser],
        'partial_update': [IsAdminUser],
        'destroy': [IsAdminUser],
        'default': [IsAuthenticated],
    }
