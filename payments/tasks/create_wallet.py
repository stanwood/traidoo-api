from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.task import IsTask
from core.tasks.mixin import TasksMixin
from payments.client.client import MangopayClient

User = get_user_model()


class CreateWalletView(views.APIView, TasksMixin):
    permission_classes = (AllowAny, IsTask)

    def post(self, request, format=None):
        user = User.objects.get(pk=request.data["user_id"])

        mangopay_client = MangopayClient(
            settings.MANGOPAY_URL,
            settings.MANGOPAY_CLIENT_ID,
            settings.MANGOPAY_PASSWORD,
        )

        mangopay_wallet = mangopay_client.create_wallet(user_id=user.mangopay_user_id)

        wallet_id = mangopay_wallet["Id"]

        self.send_task(
            f"/mangopay/tasks/create-banking-alias-iban",
            payload={"user_id": user.id, "wallet_id": wallet_id},
            queue_name="mangopay-banking-alias-iban",
            http_method="POST",
            schedule_time=5,
            headers={
                "Region": request.region.slug,
                "Content-Type": "application/json",
            },
        )

        return Response()
