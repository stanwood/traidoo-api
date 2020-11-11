import pytest
from django.db import transaction
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
