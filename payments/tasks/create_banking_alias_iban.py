from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.task import IsTask
from payments.client.client import MangopayClient

User = get_user_model()


class CreateBankingAliasIbanView(views.APIView):
    permission_classes = (AllowAny, IsTask)

    def post(self, request, format=None):
        user = User.objects.get(pk=request.data["user_id"])

        mangopay_client = MangopayClient(
            settings.MANGOPAY_URL,
            settings.MANGOPAY_CLIENT_ID,
            settings.MANGOPAY_PASSWORD,
        )

        mangopay_client.create_banking_alias_iban(
            wallet_id=request.data["wallet_id"],
            user_id=user.mangopay_user_id,
            name=user.company_name or user.get_full_name(),
        )

        return Response()
