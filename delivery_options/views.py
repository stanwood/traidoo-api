from django.conf import settings
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin
from delivery_options.models import DeliveryOption
from delivery_options.serializers import DeliveryOptionSerializer


class DeliveryOptionViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    queryset = DeliveryOption.objects.all()
    serializer_class = DeliveryOptionSerializer
    permission_classes_by_action = {'default': [IsAdminUser]}
