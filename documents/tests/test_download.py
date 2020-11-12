import datetime
from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from documents.models import Document


@pytest.fixture
def storage(storage):
    storage.from_service_account_json.return_value.get_bucket.return_value.blob.return_value.generate_signed_url.return_value = (
        "https://example.com"
    )

    yield storage


@pytest.mark.django_db
def test_buyer_download_with_incorrect_permissions(
    client_buyer, order, storage, buyer, seller
):
    buyer.is_email_verified = True
    buyer.save()

    document = baker.make(
        Document,
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id + 1},
        buyer={"user_id": buyer.id + 1},
    )

    response = client_buyer.get(f"/documents/{document.id}/download")

    assert response.status_code == 403


@pytest.mark.django_db
def test_seller_download_with_incorrect_permissions(
    client_seller, order, storage, buyer, seller
):
    seller.is_email_verified = True
    seller.save()

    document = baker.make(
        Document,
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id + 1},
        buyer={"user_id": buyer.id + 1},
    )

    response = client_seller.get(f"/documents/{document.id}/download")

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("user_type", ["buyer", "seller"])
def test_download_document(
    user_type,
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
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"user_id": seller.id if user_type == "seller" else seller.id + 1},
        buyer={"user_id": buyer.id if user_type == "buyer" else buyer.id + 1},
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
        response_disposition="inline; filename=document.pdf",
    )


def test_admin_download(db, client, order, storage, admin):
    document = baker.make(
        Document,
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"region_id": admin.region_id},
        buyer={"region_id": admin.region_id},
    )

    client.force_authenticate(user=admin)
    response = client.get(
        reverse("admin-document-download", kwargs={"document_id": document.id})
    )
    assert response.status_code == 302
    assert response.url == "https://example.com"


def test_deny_other_region_admin_download_document(
    db, client, order, storage, other_region_product, admin
):
    document = baker.make(
        Document,
        order=order,
        blob_name="documents/123/document.pdf",
        seller={"region_id": "different-region-id"},
        buyer={"region_id": "different-region-id"},
    )
    admin.is_superuser = False
    admin.save()
    client.force_authenticate(user=admin)
    response = client.get(
        reverse("admin-document-download", kwargs={"document_id": document.id})
    )
    assert response.status_code == 403
