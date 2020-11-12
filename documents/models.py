import datetime
import os
import google.cloud.storage
from enum import Enum
from typing import List

import requests
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from loguru import logger

from core.calculators.order_calculator import OrderCalculatorMixin
from core.currencies import CURRENT_CURRENCY_SYMBOL
from core.db.base import BaseAbstractModel
from documents import jinja2_utils
from orders.models import Order


class Document(OrderCalculatorMixin, BaseAbstractModel):
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    class TYPES(Enum):
        buyer_platform_invoice = (
            "Buyer Platform Invoice",
            "documents/invoice_platform.html",
        )
        platform_invoice = (
            "Platform Invoice",
            "documents/invoice_platform_producer.html",
        )
        logistics_invoice = ("Logistics Invoice", "documents/invoice_logistics.html")
        producer_invoice = ("Producer Invoice", "documents/invoice_producer.html")
        order_confirmation_buyer = (
            "Order Confirmation Buyer",
            "documents/order_confirmation_buyer.html",
        )
        delivery_overview_buyer = (
            "Delivery Overview Buyer",
            "documents/delivery_overview_buyer.html",
        )
        delivery_overview_seller = (
            "Delivery Overview Seller",
            "documents/producer_delivery_note.html",
        )
        receipt_buyer = ("Receipt Buyer", "documents/buyer_payment_receipt.html")
        credit_note = ("Credit Note", "documents/credit_note.html")

        @classmethod
        def get_value(cls, member):
            return getattr(cls, member).value[0]

        @classmethod
        def get_template(cls, document_type):
            document_config = filter(
                lambda enum_item: enum_item.value[0] == document_type, cls
            )
            return next(document_config).value[1]

    JINJA = jinja2_utils.setup_env()
    PDF_BACKEND = settings.HTML2PDF_BACKEND

    document_type = models.CharField(
        max_length=64, choices=[t.value for t in TYPES], verbose_name=_("Document type")
    )

    buyer = JSONField(null=True, blank=True, verbose_name=_("Buyer"))
    seller = JSONField(null=True, blank=True, verbose_name=_("Seller"))
    delivery_address = JSONField(
        blank=True, null=True, verbose_name=_("Delivery address")
    )
    lines = JSONField(null=True, blank=True, verbose_name=_("Invoice lines"))
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name=_("Order"),
    )
    blob_name = models.CharField(
        max_length=128, blank=True, null=True, verbose_name=_("Blob name in storage")
    )
    payment_reference = models.CharField(
        max_length=64, blank=True, null=True, verbose_name=_("Payment reference")
    )
    mangopay_payin_id = models.CharField(
        max_length=64, blank=True, null=True, verbose_name=_("Mangopay payin id")
    )
    bank_account_owner = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        default="MANGOPAY SA",
        verbose_name=_("Bank account owner"),
    )
    paid = models.BooleanField(default=False, verbose_name=_("Is paid"))

    @property
    def mangopay_tag(self):
        if self.document_type == self.TYPES.get_value("order_confirmation_buyer"):
            return f"v2 Order: {self.order_id} Buyer: {self.buyer['company_name']}"
        else:
            return (
                f"v2 Order: {self.order_id} Document: {self.document_type} "
                f"Seller: {self.seller['company_name']} "
                f"Buyer: {self.buyer['company_name']}"
            )

    @property
    def template_values(self):
        return {
            "order": self.order,
            "document": self,
            "today": localdate().strftime("%Y-%m-%d"),
            "delivery_date_feature_enabled": settings.FEATURES["delivery_date"],
            "CURRENCY_SYMBOL": CURRENT_CURRENCY_SYMBOL,
        }

    @property
    def template_name(self):
        return self.TYPES.get_template(self.document_type)

    def render_html(self):
        template = self.JINJA.get_template(self.template_name)
        return template.render(**self.template_values)

    def render_pdf(self):
        response = requests.post(
            self.PDF_BACKEND, self.render_html().encode("utf-8"), timeout=120
        )

        if response.status_code != 200:
            raise RuntimeError(response.content)  # TODO: document error

        return response.content

    @property
    def pdf_file_name(self):
        file_name, _ = os.path.splitext(os.path.split(self.template_name)[-1])

        if self.document_type == self.TYPES.get_value("producer_invoice"):
            return f"{self.order_id}-{self.id}-{file_name}_{self.seller['company_name']}.pdf"
        elif self.document_type == self.TYPES.get_value("delivery_overview_seller"):
            return f"{self.order_id}-{self.id}-{file_name}_{self.buyer['company_name']}.pdf"
        elif self.document_type == self.TYPES.get_value("logistics_invoice"):
            return f"{self.order_id}-{self.id}-{file_name}_{self.seller['company_name']}.pdf"
        elif self.document_type == self.TYPES.get_value("platform_invoice"):
            return f"{self.order_id}-{self.id}-{file_name}_{self.buyer['company_name']}.pdf"
        elif self.document_type == self.TYPES.get_value("buyer_platform_invoice"):
            return f"{self.order_id}-{self.id}-{file_name}_{self.buyer['company_name']}.pdf"

        return f"{self.order_id}-{self.id}-{file_name}.pdf"

    @property
    def calc_items(self):
        return [
            OrderCalculatorMixin.Item(
                price=line["price"],
                count=line["count"],
                vat=line["vat_rate"],
                amount=line["amount"],
                seller=line.get("seller_user_id"),
            )
            for line in self.lines
        ]

    @property
    def is_cross_region_document(self):
        return (
            len(
                {
                    self.buyer.get("region_id"),
                    self.seller.get("region_id"),
                    self.order.region_id,
                }
            )
            > 1
        )

    @property
    def receivers_emails(self) -> List[str]:
        emails = {self.seller["email"], self.buyer["email"]}

        if self.seller.get("invoice_email"):
            emails.add(self.seller.get("invoice_email"))

        if self.buyer.get("invoice_email"):
            emails.add(self.buyer.get("invoice_email"))

        if (
            self.is_cross_region_document
            and self.document_type == self.TYPES.get_value("delivery_overview_seller")
        ):
            try:
                emails.add(self.order.region.setting.logistics_company.email)
            except AttributeError:
                logger.error(
                    f"Could not find logistics company of buyer {self.buyer['user_id']} in order {self.order_id}"
                )
        return list(emails)

    @property
    def seller_company_name(self):
        return self.seller.get("company_name")

    @property
    def buyer_company_name(self):
        return self.buyer.get("company_name")

    @property
    def is_invoice(self):
        return "Invoice" in self.document_type

    @property
    def signed_download_url(self):
        storage_client = google.cloud.storage.Client.from_service_account_json(
            settings.BASE_DIR.joinpath("service_account.json")
        )

        bucket = storage_client.get_bucket(settings.DEFAULT_BUCKET)
        blob = bucket.blob(self.blob_name)

        filename = os.path.basename(self.blob_name)
        return blob.generate_signed_url(
            datetime.timedelta(minutes=settings.DOCUMENTS_EXPIRATION_TIME),
            response_disposition=f"inline; filename={filename}",
        )

    def __str__(self):
        return f"{self.document_type} #{self.order_id}"


class DocumentSendLog(BaseAbstractModel):
    """
    Model to track emails to which documents for an order were sent.
    This way we want to avoid sending duplicate mails.
    """

    email = models.EmailField()
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="document_send_logs",
        verbose_name=_("Order"),
    )
    sent = models.BooleanField(default=False)
