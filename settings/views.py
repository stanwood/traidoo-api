from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import get_region
from settings.models import GlobalSetting, Setting
from settings.serializers import GlobalSettingSerializer, SettingSerializer


class SettingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        region = get_region(self.request)
        return Response(
            SettingSerializer(Setting.objects.filter(region=region).get()).data
        )


class GlobalSettingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response(GlobalSettingSerializer(GlobalSetting.objects.first()).data)
