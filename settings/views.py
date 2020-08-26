from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin
from settings.models import GlobalSetting, Setting
from settings.serializers import GlobalSettingSerializer, SettingSerializer


class SettingViewSet(GetPermissionsMixin, viewsets.ModelViewSet):
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    pagination_class = None

    permission_classes_by_action = {
        "list": [AllowAny],
        "retrieve": [AllowAny],
        "default": [IsAdminUser],
    }


class GlobalSettingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response(GlobalSettingSerializer(GlobalSetting.objects.first()).data)
