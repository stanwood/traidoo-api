from django.contrib.auth import get_user_model
from django.core.mail import mail_admins
from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions.cron import IsCron
from core.permissions.task import IsTask
from core.tasks.mixin import TasksMixin
from payments.client.exceptions import MangopayError
from payments.crons.serializers import PayoutSerializer

from ..mixins import MangopayMixin
from ..utils import euro_to_cents

User = get_user_model()


class MangopayPayoutView(MangopayMixin, TasksMixin, views.APIView):
    permission_classes = (AllowAny, IsCron | IsTask)

    http_method_names = ["post"]

    def _create_user_bank_account(self, mangopay_user_id: str):
        user = User.objects.get(mangopay_user_id=mangopay_user_id)

        if not user.has_valid_iban:
            raise ValueError(
                f"User {user.id} has invalid iban {user.iban}. Cannot create "
                f"account in mangopay"
            )

        try:
            bank_account = self.mangopay.create_bank_account(
                mangopay_user_id,
                user.street,
                user.city,
                user.zip,
                user.company_name,
                user.iban,
            )
        except MangopayError as mangopay_error:
            logger.exception(mangopay_error)
            mail_admins(
                subject="Mangopay payout error",
                message=(
                    f"Could not create bank account in mangopay for mangopay "
                    f"user {mangopay_user_id}. Mangopay response: "
                    f"{mangopay_error}",
                ),
            )
            raise mangopay_error

        logger.debug(bank_account)

        return bank_account

    def post(self, request: Request, mangopay_user_id: str, format: str = None):
        serializer = PayoutSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = serializer.data["order_id"]
        amount = euro_to_cents(serializer.data["amount"])
        wire_reference = f"order #{order_id}" if order_id else None
        wallet = self.get_user_wallet(mangopay_user_id)
        if wallet and wallet["Balance"]["Amount"] >= amount:
            bank_account = self.get_user_bank_account(mangopay_user_id)
            if bank_account is None:
                try:
                    bank_account = self._create_user_bank_account(mangopay_user_id)
                except ValueError as value_error:
                    logger.exception(value_error)
                    return Response()

            try:
                self.mangopay.create_pay_out(
                    author_id=User.central_platform_user().mangopay_user_id,
                    amount=amount,
                    bank_account_id=bank_account["Id"],
                    wallet_id=wallet["Id"],
                    wire_reference=wire_reference,
                )
            except MangopayError as mangopay_error:
                logger.exception(mangopay_error)
                mail_admins(
                    subject="Mangopay payout Bank wire error",
                    message=(
                        f"Mangopay user {mangopay_user_id}. Mangopay "
                        f"response: {mangopay_error}"
                    ),
                )
                raise mangopay_error

        return Response()
