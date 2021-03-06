from rest_framework import generics
from rest_framework.permissions import AllowAny

from overlays.models import Overlay
from overlays.serializer import OverlaySerializer


class OverlayList(generics.ListAPIView):
    serializer_class = OverlaySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Overlay.objects.filter(region=self.request.region)
