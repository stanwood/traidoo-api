from rest_framework import generics
from rest_framework.permissions import AllowAny

from common.utils import get_region
from overlays.models import Overlay
from overlays.serializer import OverlaySerializer


class OverlayList(generics.ListAPIView):
    serializer_class = OverlaySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        region = get_region(self.request)
        return Overlay.objects.filter(region=region)
