import datetime
from unittest import mock

import pytest
from django.conf import settings
from model_bakery import baker

from documents.models import Document


@pytest.mark.django_db
def test_download_document_buyer(client_buyer, order, storage, buyer, seller):
    buyer.is_email_verified = True
    buyer.save()

    document_1 = baker.make(
        Document,
        document_type=Document.TYPES.order_confirmation_buyer.value[0],
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id + 1},
        buyer={"user_id": buyer.id},
    )

    storage.from_service_account_json.return_value.get_bucket.return_value.blob.return_value.generate_signed_url.return_value = (
        "https://example.com"
    )

    response = client_buyer.get(f"/orders/{order.id}/download")

    assert response.json() == {"url": "https://example.com", "filename": "document.pdf"}

    storage.from_service_account_json.assert_called_once_with(mock.ANY)
    storage.from_service_account_json().get_bucket.assert_called_once_with(
        settings.DEFAULT_BUCKET
    )
    storage.from_service_account_json().get_bucket().blob.assert_called_once_with(
        document_1.blob_name
    )
    storage.from_service_account_json().get_bucket().blob().generate_signed_url.assert_called_once_with(
        datetime.timedelta(seconds=60),
        response_disposition="attachment; filename=document.pdf",
    )
