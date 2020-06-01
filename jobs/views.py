import datetime

from django.db.models import Min, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.decorators.feature import require_feature

from .models import Job
from .serializers import JobSerializer


class JobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ("detour", "order_item__delivery_fee")

    def get_queryset(self):
        tomorrow = (timezone.now() + datetime.timedelta(days=1)).date()

        queryset = Job.objects.select_related(
            "order_item",
            "user",
            "order_item__order",
            "order_item__delivery_address",
            "order_item__product",
            "order_item__product__container_type",
            "order_item__product__seller",
        ).filter(
            detours__route__user=self.request.user,
            order_item__latest_delivery_date__gt=tomorrow,
        )

        if self.action == "list":
            if self.request.query_params.get("my", None) is not None:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = queryset.filter(user__isnull=True)

            queryset = (
                queryset.filter(~Q(order_item__order__processed=True))
                .annotate(detour=Min("detours__length"))
                .order_by("order_item__latest_delivery_date")
            )

        return queryset.distinct()

    @require_feature("routes")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @require_feature("routes")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @require_feature("routes")
    @action(detail=True, methods=["post", "delete"])
    def claim(self, request, pk=None):
        job = self.get_object()

        success = False

        if request.method == "POST":
            success = self._claim(job)

        if request.method == "DELETE":
            success = self._unclaim(job)

        if not success:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _claim(self, job):
        if job.user:
            return False

        if job.order_item.order.processed:
            return False

        job.user = self.request.user
        job.save()

        return True

    def _unclaim(self, job):
        if job.user != self.request.user:
            return False

        job.user = None
        job.save()

        return True
