from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.errors.exceptions import ProtectedEntityException
from delivery_addresses.models import DeliveryAddress
from delivery_addresses.serializers import DeliveryAddressSerializer


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    pagination_class = None
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryAddressSerializer

    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        try:
            return super(DeliveryAddressViewSet, self).perform_destroy(instance)
        except ProtectedError as exception:
            raise ProtectedEntityException()
