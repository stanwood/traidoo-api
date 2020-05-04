from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from taggit.models import Tag

from core.permissions.get_permissions import GetPermissionsMixin
from core.permissions.seller import IsSellerOrAdminUser
from tags.serializers import TagSerializer


class TagViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    permission_classes_by_action = {
        'create': [IsSellerOrAdminUser],
        'update': [IsSellerOrAdminUser],
        'partial_update': [IsSellerOrAdminUser],
        'destroy': [IsSellerOrAdminUser],
        'default': [AllowAny],
    }

    ordering_fields = '__all__'
