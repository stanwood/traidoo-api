import itertools
from decimal import Decimal
from typing import Dict, Optional

from django.contrib.auth import get_user_model
from django.db import transaction, OperationalError
from django.utils.decorators import method_decorator
from loguru import logger
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from common.models import Region
from core.currencies import CURRENT_CURRENCY_CODE
from core.mixins.storage import StorageMixin
from core.tasks.mixin import TasksMixin
from documents.models import Document
from mails.utils import get_admin_emails, send_mail
from orders.models import Order
from payments.client.exceptions import MangopayError, MangopayTransferError
from payments.mixins import MangopayMixin
from Traidoo.errors import PaymentError

User = get_user_model()


MANGOPAY_DOCUMENTS = {
    "IDENTITY_PROOF": "Personalausweis/Reisepass",
    "ARTICLES_OF_ASSOCIATION": "Gesellschaftervertrag/Satzung",
    "REGISTRATION_PROOF": "Nachweis der Registrierung",
    "SHAREHOLDER_DECLARATION": "Liste der Gesellschafter",
    "ADDRESS_PROOF": "Addressnachweiss",
}


class DuplicateTransferError(Exception):
    pass


def sufficient_wallet_balance_for_order(order_id, buyer_id, wallet):
    unpaid_invoices = itertools.chain(
        Document.objects.filter(
            paid=False,
            document_type__in=[
                Document.TYPES.get_value("logistics_invoice"),
                Document.TYPES.get_value("producer_invoice"),
            ],
            order_id=order_id,
        ),
        # todo: remove when there are no more unpaid buyer invoices with this type,
        # we have migrated to "buyer_platform_invoice"
        Document.objects.filter(
            paid=False,
            order_id=order_id,
            document_type=Document.TYPES.get_value("platform_invoice"),
            buyer__user_id=buyer_id
            # we consider only buyer platform invoices since
            # seller platform invoices are deducted from product invoices
        ),
        Document.objects.filter(
            paid=False,
            order_id=order_id,
            document_type=Document.TYPES.get_value("buyer_platform_invoice"),
        ),
    )

    unpaid_amount_cents = sum(invoice.price_gross_cents for invoice in unpaid_invoices)
    logger.debug(f"Unpaid amount of order {order_id} is {unpaid_amount_cents}")
    return wallet["Balance"]["Amount"] >= unpaid_amount_cents


def get_platform_user_for_order(order_id: int) -> User:
    platform_invoices = Document.objects.filter(
        order_id=order_id, document_type=Document.TYPES.get_value("platform_invoice")
    )
    invoice = platform_invoices.first()
    platform_user_id = invoice.seller["user_id"]
    return User.objects.get(pk=platform_user_id)


def calculate_platform_fee_for_order(order_id: int) -> Decimal:
    platform_invoices = Document.objects.filter(
        order_id=order_id,
        paid=False,
        document_type__in=[
            Document.TYPES.get_value("platform_invoice"),
            Document.TYPES.get_value("buyer_platform_invoice"),
        ],
    )
    platform_fees_cents = sum(
        [invoice.price_gross_cents for invoice in platform_invoices]
    )
    return Decimal(str(platform_fees_cents)) / 100


def calculate_local_platform_fee_for_order(
    order_id: int, global_platform_user_id: int
) -> Decimal:
    try:
        credit_note_for_local_platform_owner = Document.objects.get(
            order_id=order_id,
            document_type=Document.TYPES.get_value("credit_note"),
            seller__user_id=global_platform_user_id,
        )
        return Decimal(str(credit_note_for_local_platform_owner.price_gross))
    except Document.DoesNotExist:
        return Decimal("0")


def pay_for_document(
    document: Document,
    author_id: str,
    source_wallet_id: str,
    destination_wallet_id: str,
    amount: float,
    fees: float = 0,
    db="default",
):
    """
    Atomic transaction to pay for the document an mark document as paid
    :param document:
    :param author_id:
    :param source_wallet_id:
    :param destination_wallet_id:
    :param amount:
    :param fees:
    :return:
    """
    mangopay = MangopayMixin()
    with transaction.atomic(using=db):
        try:
            document = (
                Document.objects.using(db)
                .filter(id=document.id)
                .select_for_update(nowait=True)
                .get()
            )
        except OperationalError:
            raise DuplicateTransferError(
                f"Document {document.id} is being paid by other process"
            )

        if document.paid:
            raise DuplicateTransferError(f"Document {document.id} already paid")

        if source_wallet_id != destination_wallet_id and not document.paid:
            mangopay.mangopay.transfer(
                author_id,
                source_wallet_id,
                destination_wallet_id,
                amount=amount,
                fees=fees,
                tag=document.mangopay_tag,
            )
        document.paid = True
        document.save(update_fields=("paid", "updated_at"))


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class MangopayWebhookHandler(MangopayMixin, StorageMixin, TasksMixin, views.APIView):
    permission_classes = (AllowAny,)

    @property
    def event_type(self) -> str:
        return self.request.query_params.get("EventType")

    @property
    def resource_id(self) -> str:
        return self.request.query_params.get("RessourceId")

    @property
    def skip_checks(self) -> bool:
        return self.request.query_params.get("skip_checks") == "true"

    @property
    def document(self):
        try:
            document = self.mangopay.get_kyc_document(self.resource_id)
        except MangopayError:
            document = {}

        return document

    def get_region(self) -> Optional[Region]:
        if self.event_type.startswith("KYC"):
            mangopay_user_id = self.document["UserId"]
        elif self.event_type.startswith("PAYIN"):
            payin = self.mangopay.get_pay_in(self.resource_id)
            mangopay_user_id = payin["AuthorId"]
        elif self.event_type.startswith("PAYOUT"):
            payout = self.mangopay.get_pay_out(self.resource_id)
            mangopay_user_id = payout["AuthorId"]
        else:
            logger.error("Could not determine region for the request")
            return None
        try:
            return User.objects.get(mangopay_user_id=mangopay_user_id).region
        except User.DoesNotExist:
            logger.error(
                f"Could not find user with mangopay user id {mangopay_user_id}"
            )
            return None

    @staticmethod
    def document_human_name(document: Dict) -> str:
        return MANGOPAY_DOCUMENTS.get(document["Type"], document["Type"])

    @staticmethod
    def store_validation_level(user: User):
        user.mangopay_validation_level = "regular"
        user.save(update_fields=["mangopay_validation_level", "updated_at"])

    @staticmethod
    def get_user_by_mangopay_id(mangopay_user_id: str) -> User:
        return User.objects.get(mangopay_user_id=mangopay_user_id)

    def is_validation_complete(self, mangopay_user_id: str) -> bool:
        user_details = self.mangopay.get_user(mangopay_user_id)
        return user_details.get("KYCLevel") == "REGULAR"

    def document_copy_url(self, document: Dict) -> str:
        try:
            return self.get_browse_url(
                "mangopay/{}/{}".format(document["UserId"], document["Id"])
            )
        except KeyError as key_error:
            logger.error("Could not generate url to document copy")
            return ""

    def handle_valid_kyc_document(self, document: Dict):
        user = self.get_user_by_mangopay_id(document["UserId"])
        document_human_name = self.document_human_name(document)

        if self.is_validation_complete(document["UserId"]):
            logger.info("Validation complete.")
            self.store_validation_level(user)
            send_mail(
                region=self.get_region(),
                subject="Account-Verfizierung wurde erfolgreich abgeschlossen",
                recipient_list=[user.email],
                template="mails/documents/document_validated.html",
                context={
                    "document_name": document_human_name,
                    "validation_complete": True,
                    "document_url": self.document_copy_url(document),
                },
            )
        else:
            send_mail(
                region=self.get_region(),
                subject=f"{document_human_name} wurde akzeptiert",
                recipient_list=[user.email],
                template="mails/documents/document_validated.html",
                context={
                    "document_name": document_human_name,
                    "validation_complete": False,
                },
            )

    def handle_failed_kyc_document(self, document: Dict):
        user = self.get_user_by_mangopay_id(document["UserId"])
        document_human_name = self.document_human_name(document)
        send_mail(
            region=self.get_region(),
            subject=f"{document_human_name} wurde abgelehnt",
            recipient_list=[user.email],
            template="mails/documents/document_rejected.html",
            context={
                "reason_type": document["RefusedReasonType"],
                "reason_message": document["RefusedReasonMessage"],
                "document_name": document_human_name,
                "document_url": self.document_copy_url(document),
            },
        )

    def _process_as_direct_pay_in(self, pay_in: Dict):
        try:
            document = Document.objects.select_related("order").get(
                mangopay_payin_id=self.resource_id
            )
        except Document.DoesNotExist:
            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                recipient_list=get_admin_emails(),
                template="mails/generic.html",
                context={
                    "body": f"Document related to payin {self.resource_id} not found. "
                },
            )
            return

        if document.paid:
            logger.warning(
                (
                    f"Invoice `{document.id}` already paid. Probably "
                    f"duplicated notification for payin {self.resource_id} "
                    f"from mangopay. "
                )
            )
            return

        order = document.order

        pay_in_currency = pay_in["DebitedFunds"]["Currency"]
        if pay_in_currency != "EUR":
            raise PaymentError(
                (
                    f"Wrong currency `{pay_in_currency}` for payin "
                    f"{ self.resource_id}, expected EUR. "
                )
            )

        if document.document_type == document.TYPES.get_value(
            "order_confirmation_buyer"
        ):
            pay_in_amount = pay_in["DebitedFunds"]["Amount"]
            if pay_in_amount < document.price_gross_cents and not self.skip_checks:
                logger.debug(f"Document gross cents: {document.price_gross_cents}")
                send_mail(
                    region=self.get_region(),
                    subject="Fehler bei der Verarbeitung der Zahlung",
                    recipient_list=get_admin_emails(),
                    template="mails/generic.html",
                    context={
                        "body": (
                            f"Wrong amount received in payin {self.resource_id} "
                            f"for document {document.id}. Expected (in cents) "
                            f"`{document.price_gross_cents}`, but received "
                            f"`{pay_in_amount}`\n"
                        )
                    },
                )
                return Response("Falied")
            elif pay_in_amount > document.price_gross_cents and not self.skip_checks:
                logger.debug(f"Document gross cents: {document.price_gross_cents}")

                send_mail(
                    region=self.get_region(),
                    subject="Client paid too much",
                    recipient_list=get_admin_emails(),
                    template="mails/generic.html",
                    context={
                        "body": (
                            f"Too much received in payin {self.resource_id} for "
                            f"document {document.id}. Expected (in cents) "
                            f"`{document.price_gross_cents}`, but received "
                            f"`{pay_in_amount}`\n"
                        )
                    },
                )
            # Get unpaid documents for the order
            order_invoices = Document.objects.filter(
                order_id=order.id,
                paid=False,
                # Do not process platform invoices
                document_type__in=[
                    Document.TYPES.get_value("logistics_invoice"),
                    Document.TYPES.get_value("producer_invoice"),
                ],
            ).order_by("-document_type")

            for invoice in order_invoices:
                logger.debug("Paying invoice {}".format(invoice.id))
                self.pay_for_invoice_from_pay_in(pay_in, invoice)

            global_platform_user = get_platform_user_for_order(order.id)
            global_platform_user_wallet = self.get_user_wallet(
                global_platform_user.mangopay_user_id
            )

            self.pay_local_platform_owner(
                order.id,
                order.buyer.mangopay_user_id,
                pay_in["CreditedWalletId"],
                global_platform_user_wallet,
                global_platform_user.id,
            )

            # Pay combined platform fee in one transfer from buyer wallet
            try:
                self.pay_for_platform(
                    pay_in,
                    order.id,
                    order.buyer.mangopay_user_id,
                    order.total_price,
                    global_platform_user_wallet,
                    global_platform_user,
                    fees_charged_at_payin=True,
                )
            except OperationalError as error:
                logger.warning(
                    f"Other process is trying to pay for platform: `{error}`"
                )

            self.try_to_set_order_as_paid(order)

        else:
            raise PaymentError(
                "Received payment for unexpected document type {}, payin id: {}".format(
                    document.document_type, self.resource_id
                )
            )

    def handle_successful_pay_in(self):
        pay_in = self.mangopay.get_pay_in(self.resource_id)

        if pay_in["Status"] != "SUCCEEDED" and not self.skip_checks:

            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                recipient_list=get_admin_emails(),
                template="mails/generic.html",
                context={
                    "body": (
                        f"Successfully received {self.resource_id} hook, but "
                        f"actual status is `{pay_in['Status']}`. Check with Mangopay details"
                    )
                },
            )
            return

        banking_alias_id = pay_in.get("BankingAliasId")

        if not banking_alias_id:
            # Old order
            return self._process_as_direct_pay_in(pay_in)

        banking_alias = self.mangopay.get_banking_alias(banking_alias_id)

        wallet_id = banking_alias["WalletId"]
        mangopay_user_id = banking_alias["CreditedUserId"]

        buyer = User.objects.get(mangopay_user_id=mangopay_user_id)

        order_confirmation_documents = (
            Document.objects.select_related("order")
            .filter(
                paid=False,
                document_type=Document.TYPES.get_value("order_confirmation_buyer"),
                buyer__user_id=buyer.id,
                payment_reference=None,
            )
            .order_by("created_at")
        )

        for order_confirmation_document in order_confirmation_documents:
            wallet = self.mangopay.get_wallet(wallet_id)
            if not sufficient_wallet_balance_for_order(
                order_confirmation_document.order_id, buyer.id, wallet
            ):
                logger.info(
                    f"No more cash in wallet to pay for order {order_confirmation_document.order_id}"
                )
                break

            order_invoices = (
                Document.objects.select_related("order")
                .filter(
                    order_id=order_confirmation_document.order.id,
                    paid=False,
                    # Do not pay platform invoice here, since there's extra calculation
                    document_type__in=[
                        Document.TYPES.get_value("logistics_invoice"),
                        Document.TYPES.get_value("producer_invoice"),
                    ],
                )
                .order_by("-document_type")
            )

            for invoice in order_invoices:
                logger.debug("Paying invoice {}".format(invoice.id))
                self.pay_for_invoice_from_pay_in(pay_in, invoice)

            # Take the first platform invoice to get platform user information
            global_platform_user = get_platform_user_for_order(
                order_confirmation_document.order_id
            )
            if not global_platform_user.mangopay_user_id:
                error_message = (
                    f"Cannot process payin `{self.resource_id}` and pay for platform."
                    f"Platform user `{global_platform_user.id}` does not have mangopay account. "
                    f"Please create an account and process trigger payin processing again."
                )
                send_mail(
                    region=self.get_region(),
                    subject="Fehler bei der Verarbeitung der Zahlung",
                    recipient_list=get_admin_emails(),
                    template="mails/generic.html",
                    context={"body": error_message},
                )
                return

            global_platform_user_wallet = self.get_user_wallet(
                global_platform_user.mangopay_user_id
            )

            self.pay_local_platform_owner(
                order_confirmation_document.order_id,
                order_confirmation_document.order.buyer.mangopay_user_id,
                pay_in["CreditedWalletId"],
                global_platform_user_wallet,
                global_platform_user.id,
            )

            # Pay combined platform fee in one transfer from buyer wallet
            try:
                self.pay_for_platform(
                    pay_in,
                    order_confirmation_document.order.id,
                    order_confirmation_document.order.buyer.mangopay_user_id,
                    total_order_value=order_confirmation_document.price_gross,
                    global_platform_user_wallet=global_platform_user_wallet,
                    global_platform_user=global_platform_user,
                )
            except OperationalError as error:
                logger.warning(
                    f"Other process is trying to pay for platform: `{error}`"
                )

            self.try_to_set_order_as_paid(order_confirmation_document.order)

        wallet = self.mangopay.get_wallet(wallet_id)
        if wallet["Balance"]["Amount"] > 0:
            error_message = (
                f"After processing payin `{self.resource_id}` "
                f"buyer with mangopay id {mangopay_user_id} still has positive wallet"
                f"balance {wallet['Balance']['Amount']} cents"
            )
            send_mail(
                region=self.get_region(),
                subject="User has extra cash in wallet",
                recipient_list=get_admin_emails(),
                template="mails/generic.html",
                context={"body": error_message},
            )
            return

    @transaction.atomic
    def pay_local_platform_owner(
        self,
        order_id: int,
        buyer_mangopay_user_id: str,
        buyer_mangopay_wallet_id: str,
        global_platform_user_wallet: dict,
        global_platform_user_id: int,
    ) -> Decimal:
        """
        Tries to pay local platform owner
        :param global_platform_user_id:
        :param global_platform_user_wallet:
        :param buyer_mangopay_wallet_id:
        :param buyer_mangopay_user_id:
        :param order_id:
        :return: float value, amount paid for local platform owner
        """
        try:
            credit_note_for_local_platform_owner = Document.objects.get(
                order_id=order_id,
                document_type=Document.TYPES.get_value("credit_note"),
                paid=False,
                seller__user_id=global_platform_user_id,
            )
        except Document.DoesNotExist:
            logger.info(
                f"No credit notes issued by global platform owner f{global_platform_user_id}"
            )
            return Decimal("0")

        local_platform_owner = User.objects.get(
            id=credit_note_for_local_platform_owner.buyer["user_id"]
        )

        if not local_platform_owner.mangopay_user_id:
            error_message = (
                f"Cannot pay local platform owner his share {credit_note_for_local_platform_owner.price_gross} "
                f"because local platform owner `{local_platform_owner.id}` does not have mangopay account. "
                f"Funds will be transfered to global platform owner"
            )
            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                recipient_list=get_admin_emails(),
                template="mails/generic.html",
                context={"body": error_message},
            )

            # we are not using _pay_for_document() since we do not want to mark document as paid
            self.mangopay.transfer(
                buyer_mangopay_user_id,
                buyer_mangopay_wallet_id,
                global_platform_user_wallet["Id"],
                amount=credit_note_for_local_platform_owner.price_gross,
                fees=0,
                tag=credit_note_for_local_platform_owner.mangopay_tag,
            )
            return Decimal(str(credit_note_for_local_platform_owner.price_gross))

        local_platform_owner_wallet = self.get_user_wallet(
            local_platform_owner.mangopay_user_id
        )
        try:
            pay_for_document(
                document=credit_note_for_local_platform_owner,
                author_id=buyer_mangopay_user_id,
                source_wallet_id=buyer_mangopay_wallet_id,
                destination_wallet_id=local_platform_owner_wallet["Id"],
                amount=credit_note_for_local_platform_owner.price_gross,
            )
        except MangopayTransferError as mangopay_error:
            error_message = (
                f"Cannot pay local platform owner."
                f"Mangopay transfer error {mangopay_error}"
            )
            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                template="mails/generic.html",
                recipient_list=get_admin_emails(),
                context={"body": error_message},
            )
            return Decimal("0")
        except DuplicateTransferError:
            return Decimal("0")

        self.send_task(
            f"/mangopay/cron/payouts/{local_platform_owner.mangopay_user_id}",
            queue_name="mangopay-payouts",
            http_method="POST",
            payload={
                "order_id": order_id,
                "amount": credit_note_for_local_platform_owner.price_gross,
            },
            headers={
                "Region": local_platform_owner.region.slug,
                "Content-Type": "application/json",
            },
        )
        return Decimal(str(credit_note_for_local_platform_owner.price_gross))

    @transaction.atomic
    def pay_for_platform(
        self,
        pay_in: Dict,
        order_id: int,
        buyer_mangopay_user_id: str,
        total_order_value: float,
        global_platform_user_wallet: dict,
        global_platform_user: User,
        fees_charged_at_payin=False,
    ):
        platform_invoices = Document.objects.select_for_update(nowait=True).filter(
            order_id=order_id,
            paid=False,
            document_type__in=[
                Document.TYPES.get_value("platform_invoice"),
                Document.TYPES.get_value("buyer_platform_invoice"),
            ],
        )

        invoice = platform_invoices.first()
        if not invoice:
            return

        local_platform_fee_due = calculate_local_platform_fee_for_order(
            order_id, global_platform_user.id
        )
        buyer_mangopay_wallet_id = pay_in["CreditedWalletId"]
        global_platform_user_mangopay_id = global_platform_user_wallet["Owners"][0]
        total_unpaid_platform_invoices_value = calculate_platform_fee_for_order(
            order_id
        )
        mangopay_fees = self.mangopay_fees(total_order_value)
        mangopay_fees = Decimal(str(mangopay_fees))

        amount_to_transfer_to_global_platform_owner = (
            total_unpaid_platform_invoices_value - local_platform_fee_due
        )

        amount_to_payout_from_global_platform_owner_wallet = (
            amount_to_transfer_to_global_platform_owner - mangopay_fees
        )

        if fees_charged_at_payin:
            amount_to_transfer_to_global_platform_owner -= mangopay_fees

        amount_to_transfer_to_global_platform_owner = (
            amount_to_transfer_to_global_platform_owner.quantize(
                Decimal(".01"), "ROUND_HALF_UP"
            )
        )

        amount_to_transfer_to_global_platform_owner = float(
            amount_to_transfer_to_global_platform_owner
        )

        try:
            # not using `pay_for_document` to avoid nested transactions
            self.mangopay.transfer(
                buyer_mangopay_user_id,
                buyer_mangopay_wallet_id,
                global_platform_user_wallet["Id"],
                amount=amount_to_transfer_to_global_platform_owner,
                fees=float(mangopay_fees) if not fees_charged_at_payin else 0,
                tag=invoice.mangopay_tag,
            )
        except MangopayTransferError as transfer_error:
            error_message = (
                f"Transfer from buyer wallet {buyer_mangopay_wallet_id} to "
                f"platform wallet {global_platform_user_wallet['Id']} failed. "
                f"Mangopay error: {transfer_error}. "
            )
            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                template="mails/generic.html",
                context={"body": error_message},
                recipient_list=get_admin_emails(),
            )
            return

        for invoice in platform_invoices:
            invoice.paid = True
            invoice.save(update_fields=["paid", "updated_at"])

            send_mail(
                region=self.get_region(),
                subject=f"Zahlung erhalten für Auftrag #{invoice.order_id}",
                template="mails/payments/successful_payin.html",
                context={
                    "currency": CURRENT_CURRENCY_CODE,
                    "amount": f"{invoice.price_gross:.2f}",
                    "buyer_company_name": invoice.buyer["company_name"],
                    "document_name": invoice.__class__.__name__,
                    "order_number": invoice.order_id,
                },
                recipient_list=[invoice.seller["email"]],
            )

        self.send_task(
            f"/mangopay/cron/payouts/{global_platform_user_mangopay_id}",
            queue_name="mangopay-payouts",
            http_method="POST",
            payload={
                "order_id": invoice.order_id,
                "amount": float(amount_to_payout_from_global_platform_owner_wallet),
            },
            headers={
                "Region": invoice.order.region.slug,
                "Content-Type": "application/json",
            },
        )

    def pay_for_invoice_from_pay_in(self, pay_in: Dict, invoice: Document):
        seller_id = invoice.seller["user_id"]
        buyer_id = invoice.buyer["user_id"]

        seller_profile = User.objects.get(pk=seller_id)
        if not seller_profile.mangopay_user_id:
            error_message = (
                f"Cannot process payin `{self.resource_id}`. Seller "
                f"`{seller_id}` does not have mangopay account. "
                f"Please create an account and contact support to trigger order processing again"
            )
            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                template="mails/generic.html",
                context={"body": error_message},
                recipient_list=get_admin_emails(),
            )
            return

        seller_mangopay_wallet = self.get_user_wallet(seller_profile.mangopay_user_id)

        buyer_profile = User.objects.get(pk=buyer_id)
        buyer_mangopay_wallet_id = pay_in["CreditedWalletId"]

        if invoice.document_type == invoice.TYPES.get_value("producer_invoice"):
            # Producer gets paid for invoice minus gross value of platform
            # invoice for his sale
            platform_invoice_for_this_producer = Document.objects.get(
                order_id=invoice.order.id,
                document_type=Document.TYPES.get_value("platform_invoice"),
                buyer__user_id=seller_id,
            )
            amount = Decimal(str(invoice.price_gross)) - Decimal(
                str(platform_invoice_for_this_producer.price_gross)
            )
        else:
            amount = Decimal(str(invoice.price_gross))
        amount = amount.quantize(Decimal(".01"), "ROUND_HALF_UP")
        amount = float(amount)

        try:
            pay_for_document(
                document=invoice,
                author_id=buyer_profile.mangopay_user_id,
                source_wallet_id=buyer_mangopay_wallet_id,
                destination_wallet_id=seller_mangopay_wallet["Id"],
                amount=amount,
                fees=0,
            )
        except MangopayTransferError as mangopay_error:
            error_message = (
                f"Transfer from buyer wallet {buyer_mangopay_wallet_id} to "
                f"seller wallet {seller_mangopay_wallet['Id']} failed. "
                f"Mangopay error: {mangopay_error}. "
                "Please contact support to investigate issue and trigger processing again."
                f"Affected document {invoice.id}"
            )
            send_mail(
                region=self.get_region(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                template="mails/generic.html",
                context={"body": error_message},
                recipient_list=get_admin_emails(),
            )
            return
        except DuplicateTransferError as error:
            logger.exception(error)
            return

        send_mail(
            region=self.get_region(),
            subject=f"Zahlung erhalten für Auftrag #{invoice.order_id}",
            template="mails/payments/successful_payin.html",
            context={
                "currency": CURRENT_CURRENCY_CODE,
                "amount": f"{amount:.2f}",
                "buyer_company_name": invoice.buyer["company_name"],
                "document_name": invoice.__class__.__name__,
                "order_number": invoice.order_id,
            },
            recipient_list=[invoice.seller["email"]],
        )

        self.send_task(
            f"/mangopay/cron/payouts/{seller_profile.mangopay_user_id}",
            queue_name="mangopay-payouts",
            http_method="POST",
            payload={"order_id": invoice.order_id, "amount": amount},
            headers={
                "Region": invoice.order.region.slug,
                "Content-Type": "application/json",
            },
        )

    @staticmethod
    def try_to_set_order_as_paid(order: Order):
        unpaid_invoices = order.documents.filter(
            document_type__icontains="Invoice", paid=False
        ).exists()

        if not unpaid_invoices:
            logger.info("All invoices paid. Setting order as paid")

            order.set_paid()
            order.save(update_fields=["status", "updated_at"])

            try:
                order_confirmation = order.documents.get(
                    document_type=Document.TYPES.get_value("order_confirmation_buyer"),
                    paid=False,
                )
            except Document.DoesNotExist:
                logger.exception(
                    f"Failed to set Order Confirmation document as paid for "
                    f"order {order.id}. Document not found"
                )
            else:
                order_confirmation.paid = True
                order_confirmation.save(update_fields=["paid", "updated_at"])

    def handle_failed_payin(self):
        payin = self.mangopay.get_pay_in(self.resource_id)
        if payin["Status"] == "FAILED":
            body = (
                f"Payin {self.resource_id} failed. Error message: "
                f"{payin['ResultMessage']}. Check mangopay for further details."
            )
            logger.debug(f"handle_failed_payin: {body}")
            send_mail(
                region=self.get_region(),
                recipient_list=get_admin_emails(),
                subject="Fehler bei der Verarbeitung der Zahlung",
                template="mails/generic.html",
                context={"body": body},
            )

    def handle_successful_payout(self):
        payout = self.mangopay.get_pay_out(self.resource_id)

        if payout["DebitedWalletId"] == "FEES_EUR":
            logger.info("Mangopay fees payout. Ignoring")
            return

        if payout["Status"] == "SUCCEEDED":
            wallet = self.mangopay.get_wallet(payout["DebitedWalletId"])
            user = self.get_user_by_mangopay_id(wallet["Owners"][0])
            amount = "{0:.2f}".format(payout["CreditedFunds"]["Amount"] / 100.0)
            currency = payout["CreditedFunds"]["Currency"]
            send_mail(
                region=self.get_region(),
                template="mails/payments/successful_payout.html",
                context={"amount": amount, "currency": currency},
                recipient_list=[user.email],
                subject="Beträge wurden überwiesen",
            )
        else:
            logger.error("Weird, hook status different than real payout status")

    def handle_failed_payout(self):
        payout = self.mangopay.get_pay_out(self.resource_id)
        if payout["Status"] != "SUCCEEDED":
            wallet = self.mangopay.get_wallet(payout["DebitedWalletId"])
            user = self.get_user_by_mangopay_id(mangopay_user_id=wallet["Owners"][0])
            amount = "{0:.2f}".format(payout["CreditedFunds"]["Amount"] / 100.0)
            currency = payout["CreditedFunds"]["Currency"]
            result_message = payout["ResultMessage"]
            send_mail(
                region=self.get_region(),
                template="mails/payments/failed_payout.html",
                context={
                    "amount": amount,
                    "currency": currency,
                    "result_message": result_message,
                },
                recipient_list=[user.email],
                subject="Eine Überweisung ist fehlgeschlagen",
            )
        else:
            logger.error("Weird, hook status different than real payout status")

    def get(self, request: Request, format: str = None):
        # figure out region from mangopay object
        if self.event_type.startswith("KYC"):
            document = self.document
            if self.event_type == "KYC_SUCCEEDED" and document["Status"] == "VALIDATED":
                self.handle_valid_kyc_document(document)
            if self.event_type == "KYC_FAILED" and document["Status"] == "REFUSED":
                self.handle_failed_kyc_document(document)
        if self.event_type == "PAYIN_NORMAL_SUCCEEDED":
            self.handle_successful_pay_in()
        if self.event_type == "PAYIN_NORMAL_FAILED":
            self.handle_failed_payin()
        if self.event_type == "PAYOUT_NORMAL_SUCCEEDED":
            self.handle_successful_payout()
        if self.event_type == "PAYOUT_NORMAL_FAILED":
            self.handle_failed_payout()

        return Response("Webhook complete")
