from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.client.client import MangopayClient
from users.serializers import TokenUidSerializer


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = TokenUidSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user
        user.is_active = True
        user.is_email_verified = True
        user.save()

        mangopay_client = MangopayClient(
            settings.MANGOPAY_URL,
            settings.MANGOPAY_CLIENT_ID,
            settings.MANGOPAY_PASSWORD,
        )

        mangopay_wallet = mangopay_client.create_wallet(user_id=user.mangopay_user_id)

        wallet_id = mangopay_wallet.get("Id")
        if not wallet_id:
            return

        mangopay_client.create_banking_alias_iban(
            wallet_id=wallet_id,
            user_id=user.mangopay_user_id,
            name=user.get_full_name(),
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
