from rest_framework import viewsets

from common.utils import get_region

from .models import Region
from .serializers import RegionSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RegionSerializer

    def get_queryset(self):
        region = get_region(self.request)
        return Region.objects.exclude(slug=region.slug)
