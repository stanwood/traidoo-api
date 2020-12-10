from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from .models import Region
from .serializers import RegionSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RegionSerializer

    def get_queryset(self):
        return Region.objects.exclude(id=self.request.region.id)


class StaticViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Region.objects.get(slug=self.request.region.slug)

    @action(detail=False, methods=["get"])
    def terms_of_services(self, request):
        return Response({"body": self.get_queryset().terms_of_services})

    @action(detail=False, methods=["get"])
    def privacy_policy(self, request):
        return Response({"body": self.get_queryset().privacy_policy})

    @action(detail=False, methods=["get"])
    def prices(self, request):
        return Response({"body": self.get_queryset().prices})

    @action(detail=False, methods=["get"])
    def contact(self, request):
        return Response({"body": self.get_queryset().contact})

    @action(detail=False, methods=["get"])
    def imprint(self, request):
        return Response({"body": self.get_queryset().imprint})
