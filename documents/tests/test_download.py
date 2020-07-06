import datetime
from unittest import mock

import pytest
from django.conf import settings
from model_bakery import baker

from documents.models import Document
from documents.utils.document_types import (
    get_buyer_document_types,
    get_seller_document_types,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "document_type,cooperative",
    [
        (Document.TYPES.buyer_platform_invoice, False),
        (Document.TYPES.platform_invoice, False,),
        (Document.TYPES.platform_invoice, True,),
        (Document.TYPES.delivery_overview_seller, False),
        (Document.TYPES.delivery_overview_seller, True),
        (Document.TYPES.receipt_buyer, False),
        (Document.TYPES.receipt_buyer, True),
        (Document.TYPES.credit_note, False),
        (Document.TYPES.credit_note, True),
    ],
)
def test_buyer_download_with_incorrect_permissions(
    document_type, cooperative, client_buyer, order, storage, buyer, seller
):
    buyer.is_email_verified = True
    buyer.is_cooperative_member = cooperative
    buyer.save()

    document = baker.make(
        Document,
        document_type=document_type.value[0],
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id + 1},
        buyer={"user_id": buyer.id},
    )

    assert not document_type.value[0] in get_buyer_document_types(buyer)

    response = client_buyer.get(f"/documents/{document.id}/download")

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "document_type",
    [
        Document.TYPES.buyer_platform_invoice,
        Document.TYPES.logistics_invoice,
        Document.TYPES.delivery_overview_buyer,
        Document.TYPES.order_confirmation_buyer,
        Document.TYPES.receipt_buyer,
        Document.TYPES.credit_note,
    ],
)
def test_seller_download_with_incorrect_permissions(
    document_type, client_seller, order, storage, buyer, seller
):
    seller.is_email_verified = True
    seller.save()

    document = baker.make(
        Document,
        document_type=document_type.value[0],
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id + 1},
        buyer={"user_id": buyer.id},
    )

    assert not document_type.value[0] in get_seller_document_types()

    response = client_seller.get(f"/documents/{document.id}/download")

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_type,document_type,cooperative",
    [
        ("buyer", Document.TYPES.buyer_platform_invoice, True),
        ("buyer", Document.TYPES.producer_invoice, False),
        ("buyer", Document.TYPES.logistics_invoice, True),
        ("buyer", Document.TYPES.delivery_overview_buyer, False),
        ("buyer", Document.TYPES.order_confirmation_buyer, True),
        ("seller", Document.TYPES.producer_invoice, True),
        ("seller", Document.TYPES.platform_invoice, False),
        ("seller", Document.TYPES.delivery_overview_seller, True),
    ],
)
def test_download_document(
    user_type,
    document_type,
    cooperative,
    client_buyer,
    client_seller,
    order,
    storage,
    buyer,
    seller,
):
    user = buyer if user_type == "buyer" else seller
    client = client_buyer if user_type == "buyer" else client_seller

    user.is_email_verified = True
    user.save()

    document = baker.make(
        Document,
        document_type=document_type.value[0],
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id},
        buyer={"user_id": buyer.id},
    )

    storage.from_service_account_json.return_value.get_bucket.return_value.blob.return_value.generate_signed_url.return_value = (
        "https://example.com"
    )

    response = client.get(f"/documents/{document.id}/download")

    assert response.json() == {"url": "https://example.com", "filename": "document.pdf"}

    storage.from_service_account_json.assert_called_once_with(mock.ANY)
    storage.from_service_account_json().get_bucket.assert_called_once_with(
        settings.DEFAULT_BUCKET
    )
    storage.from_service_account_json().get_bucket().blob.assert_called_once_with(
        document.blob_name
    )
    storage.from_service_account_json().get_bucket().blob().generate_signed_url.assert_called_once_with(
        datetime.timedelta(seconds=60),
        response_disposition="attachment; filename=document.pdf",
    )
