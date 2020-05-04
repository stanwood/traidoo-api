from django.contrib.auth.models import Group
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin
from groups.serializers import GroupSerializer


class GroupViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'default': [IsAdminUser],
    }

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
