import datetime

import pytest
import pytz
from django.db import transaction
from freezegun import freeze_time
from model_bakery import baker

from documents.models import Document
from payments.views import DuplicateTransferError, pay_for_document


def test_document_already_paid(producer_invoice, mangopay):
    producer_invoice.paid = True
    producer_invoice.save()

    with pytest.raises(DuplicateTransferError):
        pay_for_document(
            document=producer_invoice,
            author_id="user-1",
            source_wallet_id="wallet-1",
            destination_wallet_id="wallet-2",
            amount=10,
            fees=0,
        )

    mangopay.transfer.assert_not_called()


def test_document_updated_at_after_payment(producer_invoice, mangopay):
    with freeze_time("2021-02-05"):
        pay_for_document(
            document=producer_invoice,
            author_id="user-1",
            source_wallet_id="wallet-1",
            destination_wallet_id="wallet-2",
            amount=10,
            fees=0,
        )

    producer_invoice.refresh_from_db()
    assert producer_invoice.updated_at == datetime.datetime(2021, 2, 5, tzinfo=pytz.UTC)


def test_stop_concurrent_payment(transactional_db, mangopay):
    producer_invoice = baker.make_recipe("documents.producer_invoice", paid=False)

    with transaction.atomic():
        Document.objects.filter(id=producer_invoice.id).select_for_update(
            nowait=True
        ).get()
        with transaction.atomic(using="alternate"):
            with pytest.raises(DuplicateTransferError):
                pay_for_document(
                    document=producer_invoice,
                    author_id="user-1",
                    source_wallet_id="wallet-1",
                    destination_wallet_id="wallet-2",
                    amount=10,
                    fees=0,
                    db="alternate",
                )
