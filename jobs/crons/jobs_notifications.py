import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Min
from django.utils import timezone
from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.currencies import CURRENT_CURRENCY_SYMBOL
from core.decorators.feature import require_feature
from core.permissions.cron_or_task import IsCronOrTask
from core.tasks.mixin import TasksMixin
from mails.utils import send_mail

from ..models import Job

User = get_user_model()


class JobsNotificationsView(TasksMixin, views.APIView):
    permission_classes = (AllowAny, IsCronOrTask)

    @require_feature("routes")
    def get(self, request, format=None):
        seller_group = Group.objects.get(name="seller")

        for user in User.objects.filter(
            is_email_verified=True,
            is_active=True,
            routes__isnull=False,
            groups__in=[seller_group],
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
        tomorrow = (timezone.now() + datetime.timedelta(days=1)).date()

        jobs_queryset = (
            Job.objects.prefetch_related("detours")
            .filter(
                detours__route__user_id=user_id,
                order_item__latest_delivery_date__gt=tomorrow,
                user__isnull=True,
                order_item__order__processed=False,
            )
            .annotate(detour=Min("detours__length"))
            .order_by("order_item__latest_delivery_date")
            .distinct()
        )

        if jobs_queryset.count() < 1:
            logger.debug(f"No jobs for user {user_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        send_mail(
            request.region,
            subject="Routes",
            recipient_list=[user.email],
            template="mails/jobs/notification_email.html",
            context={"jobs": jobs_queryset, "CURRENCY_SYMBOL": CURRENT_CURRENCY_SYMBOL},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
