import itertools
from decimal import Decimal
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from core.mixins.storage import StorageMixin
from core.tasks.mixin import TasksMixin
from delivery_options.models import DeliveryOption
from documents import factories
from documents.models import Document, DocumentSendLog
from orders.models import Order
from payments.mixins import MangopayMixin
from Traidoo import errors

User = get_user_model()


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class DocumentsTask(MangopayMixin, StorageMixin, TasksMixin, views.APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def invoices(order: Order, sellers: List[User]):
        documents = []

        # Add platform invoice for a buyer only if he is not a cooperative
        # member
        if not order.buyer.is_cooperative_member:
            documents.append(
                factories.BuyerPlatformInvoiceFactory(
                    order, region=order.buyer.region
                ).compose()
            )

        if order.has_central_logistics_deliveries:
            regions = {
                order_item.product.region
                for order_item in order.items.select_related("product__region")
                .filter(delivery_option__id=DeliveryOption.CENTRAL_LOGISTICS)
                .distinct()
            }

            for region in regions:
                documents.append(
                    factories.LogisticsInvoiceFactory(order, region=region).compose()
                )

        if settings.FEATURES["routes"] and order.has_third_party_deliveries:
            logger.debug("Generating invoice for a supplier.")

            regions = {
                order_item.product.region
                for order_item in order.items.select_related("product__region")
                .filter(job__user__isnull=False)
                .distinct()
            }

            for region in regions:
                for document in factories.ThirdPartyLogisticsInvoiceFactory(
                    order, region=region
                ).compose():
                    documents.append(document)

        for seller in sellers:
            documents.extend(
                [
                    factories.ProducerInvoiceFactory(
                        order, region=seller.region, seller=seller
                    ).compose(),
                    factories.PlatformInvoiceFactory(
                        order, region=seller.region, seller=seller
                    ).compose(),
                ]
            )

        return documents

    @staticmethod
    def delivery_documents(order: Order, sellers: List[User]):
        documents = []

        documents.append(
            factories.DeliveryOverviewBuyerFactory(order, region=order.region).compose()
        )

        for seller in sellers:
            documents.append(
                factories.DeliveryOverviewSellerFactory(
                    order, region=seller.region, seller=seller
                ).compose()
            )

        # hide IBAN from delivery documents
        for document in documents:
            document.seller["iban"] = None

        return documents

    def _add_iban_alias_to_order_confirmation(
        self, order_confirmation: Document, order: Order
    ):
        wallet = self.get_user_wallet(order.buyer.mangopay_user_id)
        wallet_id = wallet.get("Id")

        # List that contains only one item maximum
        banking_alias = self.get_wallet_banking_alias(wallet_id)

        if banking_alias:
            iban = banking_alias["iban"]
            bic = banking_alias["bic"]
            owner_name = banking_alias["owner_name"]
        else:
            banking_alias = self.mangopay.create_banking_alias_iban(
                user_id=order.buyer.mangopay_user_id,
                wallet_id=wallet_id,
                name=order.buyer.get_full_name(),
            )
            iban = banking_alias["IBAN"]
            bic = banking_alias["BIC"]
            owner_name = banking_alias["OwnerName"]

        order_confirmation.seller["iban"] = iban
        order_confirmation.seller["bic"] = bic
        order_confirmation.bank_account_owner = owner_name
        order_confirmation.save()

    @transaction.atomic
    def create_documents(self, order):
        sellers = {item.product.seller for item in order.items.all()}

        order_confirmation = factories.OrderConfirmationBuyerFactory(
            order, region=order.region
        ).compose()

        documents = list(
            itertools.chain(
                self.invoices(order, sellers),
                self.delivery_documents(order, sellers),
                [order_confirmation],
            )
        )

        if (
            order.settings.platform_user
            and order.settings.enable_platform_fee_share
            and order.settings.central_share
            and order.settings.central_share < Decimal("100")
        ):
            credit_note = factories.CreditNoteFactory(
                order, region=order.region
            ).compose()
            documents.append(credit_note)

        if not order_confirmation.mangopay_payin_id:
            self._add_iban_alias_to_order_confirmation(order_confirmation, order)

        for document in documents:
            if "Invoice" in document.document_type:
                document.seller["iban"] = (
                    "Bitte nutzen Sie die Kontodaten in der "
                    "Bestellzusammenfassung zur Zahlung aller Rechnungen "
                    "dieser Bestellung."
                )
                document.seller["bic"] = None
                document.seller["bank"] = None

        logger.debug(f"Number of documents: {len(documents)}.")
        [document.save() for document in documents]
        return documents

    def create_document_sending_tasks(self, documents, order):
        emails = itertools.chain(*[document.receivers_emails for document in documents])
        emails = set(emails)
        for email in emails:
            with transaction.atomic():
                DocumentSendLog.objects.get_or_create(
                    email=email, order_id=order.id, sent=False
                )
                self.send_task(
                    reverse(
                        "mail-documents", kwargs={"order_id": order.id, "email": email}
                    ),
                    queue_name="document-emails",
                )

    def render_pdfs(self, documents, order):
        pdfs = [document.render_pdf() for document in documents]
        stored_blobs = [
            self._store(f"documents/{order.id}/{document.pdf_file_name}", data)
            for document, data in zip(documents, pdfs)
        ]
        logger.debug(f"Number of stored PDF files: {len(stored_blobs)}.")
        for document, blob in zip(documents, stored_blobs):
            document.blob_name = blob.name
        [document.save(update_fields=["blob_name"]) for document in documents]
        return stored_blobs

    def post(
        self, request: Request, order_id: str, document_set: str, format: str = None
    ):
        order_id = int(order_id)

        try:
            order = (
                Order.objects.select_related("buyer__region", "region")
                .prefetch_related("items__product__seller")
                .get(pk=order_id)
            )
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if order.buyer.mangopay_user_id is None:
            raise errors.PaymentError(
                f"Buyer {order.buyer.id} does not have mangopay account. "
                f"Admin should activate his account"
            )

        documents = self.create_documents(order)
        self.render_pdfs(documents, order)
        self.create_document_sending_tasks(documents, order)

        order.processed = True
        order.save()
        order.recalculate_items_delivery_fee()

        return Response("Documents created")
