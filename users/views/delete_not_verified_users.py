import datetime

from django.conf import settings
from django.utils import timezone
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.cron import IsCron

from ..models import User


class DeleteNotVerifiedUsersView(views.APIView):
    permission_classes = (
        AllowAny,
        IsCron,
    )

    @classmethod
    def get_latest_update_time(cls):
        return timezone.now() - datetime.timedelta(minutes=settings.UNVERIFIED_USER_LIFE_HOURS)

    @classmethod
    def get(self, request, format=None):
        User.objects.filter(
            updated_at__lt=self.get_latest_update_time(),
            is_email_verified=False,
        ).delete()
        return Response()
