from rest_framework import generics
from rest_framework.permissions import AllowAny

from overlays.models import Overlay
from overlays.serializer import OvertlaySerializer


class OverlayList(generics.ListAPIView):
    queryset = Overlay.objects.all()
    serializer_class = OvertlaySerializer
    permission_classes = [AllowAny]
    pagination_class = None
