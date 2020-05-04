import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Min
from django.template.loader import render_to_string
from django.utils import timezone
from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.utils import get_region
from core.decorators.feature import require_feature
from core.permissions.cron_or_task import IsCronOrTask
from core.tasks.mixin import TasksMixin
from mails.utils import send_mail

from ..models import Detour, Job

User = get_user_model()


class JobsNotificationsView(TasksMixin, views.APIView):
    permission_classes = (AllowAny, IsCronOrTask)

    @require_feature("routes")
    def get(self, request, format=None):
        for user in User.objects.filter(
            is_email_verified=True, is_active=True, routes__isnull=False
        ).distinct():
            self.send_task(
                f"/jobs/cron/notifications/{user.id}",
                queue_name="emails",
                http_method="POST",
                headers={"Region": user.region.slug},
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @require_feature("routes")
    def post(self, request, user_id, format=None):
        user = User.objects.get(id=user_id)

        jobs_queryset = (
            Job.objects.prefetch_related("detours")
            .filter(
                detours__route__user_id=user_id,
                order_item__latest_delivery_date__gt=timezone.now()
                + datetime.timedelta(days=1),
                user__isnull=True,
            )
            .annotate(detour=Min("detours__length"))
            .order_by("order_item__latest_delivery_date")
            .distinct()
        )

        if jobs_queryset.count() < 1:
            logger.debug(f"No jobs for user {user_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        send_mail(
            get_region(request),
            subject="Routes",
            recipient_list=[user.email],
            template="mails/jobs/notification_email.html",
            context={"jobs": jobs_queryset},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
