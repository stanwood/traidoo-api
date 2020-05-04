from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin
from settings.models import Setting
from settings.serializers import SettingSerializer


class SettingViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    pagination_class = None

    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'default': [IsAdminUser],
    }
