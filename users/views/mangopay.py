from django.contrib.auth import get_user_model
from loguru import logger
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.task import IsTask
from core.tasks.mixin import TasksMixin
from payments.mixins import MangopayMixin
from users.models import KycDocument

User = get_user_model()


class CreateMangopayAccountView(MangopayMixin, TasksMixin, views.APIView):
    permission_classes = (AllowAny, IsTask)

    def post(self, request, user_id, format=None):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} does not exist.")

        self.create_mangopay_account_for_user(user)

        for document in KycDocument.objects.filter(user=user):
            self.send_task(
                f"/users/mangopay/documents/{document.id}",
                queue_name="documents",
                http_method="POST",
                schedule_time=20,
                headers={"Region": user.region.slug},
            )

        return Response()
