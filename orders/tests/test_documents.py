import datetime
from unittest import mock

import pytest
from django.conf import settings
from model_mommy import mommy

from documents.models import Document
from orders.models import Order


@pytest.mark.django_db
def test_get_order_documents_anonymous(client_anonymous, client, order):
    response = client_anonymous.get(f'/orders/{order.id}/documents')
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_order_no_groups(client, order):
    response = client.get(f'/orders/{order.id}/documents')
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_order_documents_seller(client_seller, seller):
    order_1 = mommy.make(Order)
    document_1 = mommy.make(Document, order=order_1, seller={'user_id': seller.id})
    document_2 = mommy.make(Document, order=order_1, seller={'user_id': seller.id})

    order_2 = mommy.make(Order)
    mommy.make(Document, order=order_2, seller={'user_id': seller.id + 1})
    mommy.make(Document, order=order_1, seller={'user_id': seller.id + 1})

    response = client_seller.get(f'/orders/{order_1.id}/documents')

    assert set([document['id'] for document in response.json()]) == set(
        [document_1.id, document_2.id]
    )


@pytest.mark.django_db
def test_get_order_documents_buyer_admin(client_buyer, client_admin, seller):
    order_1 = mommy.make(Order)
    document_1 = mommy.make(Document, order=order_1, seller={'user_id': seller.id})
    document_2 = mommy.make(Document, order=order_1, seller={'user_id': seller.id})

    order_2 = mommy.make(Order)
    mommy.make(Document, order=order_2, seller={'user_id': seller.id + 1})
    document_3 = mommy.make(Document, order=order_1, seller={'user_id': seller.id + 1})

    response = client_buyer.get(f'/orders/{order_1.id}/documents')

    assert set([document['id'] for document in response.json()]) == set(
        [document_1.id, document_2.id, document_3.id]
    )

    response = client_admin.get(f'/orders/{order_1.id}/documents')

    assert set([document['id'] for document in response.json()]) == set(
        [document_1.id, document_2.id, document_3.id]
    )


@pytest.mark.django_db
def test_get_single_document_buyer(client_buyer, order, buyer, seller):
    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/file.pdf',
        seller={'user_id': seller.id + 1},
    )

    response = client_buyer.get(f'/orders/{order.id}/documents/{document_1.id}')

    assert response.json() == {
        'id': document_1.id,
        'documentType': document_1.document_type,
        'filename': 'file.pdf',
    }


@pytest.mark.django_db
def test_get_single_document_seller_no_permissions(client_seller, order, buyer, seller):
    seller.is_email_verified = True
    seller.save()

    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/file.pdf',
        seller={'user_id': seller.id + 1},
    )

    response = client_seller.get(f'/orders/{order.id}/documents/{document_1.id}')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Not found.'}


@pytest.mark.django_db
def test_get_single_document_buyer_admin(
    client_buyer, client_admin, order, buyer, seller, admin
):
    buyer.is_email_verified = True
    buyer.save()

    admin.is_email_verified = True
    admin.save()

    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/file.pdf',
        seller={'user_id': seller.id + 1},
    )

    response = client_buyer.get(f'/orders/{order.id}/documents/{document_1.id}')

    assert response.json() == {
        'id': document_1.id,
        'documentType': document_1.document_type,
        'filename': 'file.pdf',
    }

    response = client_admin.get(f'/orders/{order.id}/documents/{document_1.id}')

    assert response.json() == {
        'id': document_1.id,
        'documentType': document_1.document_type,
        'filename': 'file.pdf',
    }


@pytest.mark.django_db
def test_download_document_buyer(client_buyer, order, storage, buyer, seller):
    buyer.is_email_verified = True
    buyer.save()

    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/document.pdf',
        seller={'user_id': seller.id + 1},
    )

    storage.from_service_account_json.return_value.get_bucket.return_value.blob.return_value.generate_signed_url.return_value = (
        'https://example.com'
    )

    response = client_buyer.get(
        f'/orders/{order.id}/documents/{document_1.id}/download'
    )

    assert response.json() == {'url': 'https://example.com', 'filename': 'document.pdf'}

    storage.from_service_account_json.assert_called_once_with(mock.ANY)
    storage.from_service_account_json().get_bucket.assert_called_once_with(
        settings.DEFAULT_BUCKET
    )
    storage.from_service_account_json().get_bucket().blob.assert_called_once_with(
        document_1.blob_name
    )
    storage.from_service_account_json().get_bucket().blob().generate_signed_url.assert_called_once_with(
        datetime.timedelta(seconds=60),
        response_disposition='attachment; filename=document.pdf',
    )


@pytest.mark.django_db
def test_download_document_seller_no_permissions(
    client_seller, order, storage, buyer, seller
):
    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/document.pdf',
        seller={'user_id': seller.id + 1},
    )

    response = client_seller.get(
        f'/orders/{order.id}/documents/{document_1.id}/download'
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_download_document_no_permissions(client, order, storage, buyer, seller):
    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/document.pdf',
        seller={'user_id': seller.id + 1},
    )

    response = client.get(f'/orders/{order.id}/documents/{document_1.id}/download')

    assert response.status_code == 401


@pytest.mark.django_db
def test_download_document_anonymous(client_anonymous, order, storage, buyer, seller):
    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/document.pdf',
        seller={'user_id': seller.id + 1},
    )

    response = client_anonymous.get(
        f'/orders/{order.id}/documents/{document_1.id}/download'
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_download_document_seller(client_seller, order, storage, buyer, seller):
    seller.is_email_verified = True
    seller.save()

    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/document.pdf',
        seller={'user_id': seller.id},
    )

    storage.from_service_account_json.return_value.get_bucket.return_value.blob.return_value.generate_signed_url.return_value = (
        'https://example.com'
    )

    response = client_seller.get(
        f'/orders/{order.id}/documents/{document_1.id}/download'
    )

    assert response.json() == {'url': 'https://example.com', 'filename': 'document.pdf'}

    storage.from_service_account_json.assert_called_once_with(mock.ANY)
    storage.from_service_account_json().get_bucket.assert_called_once_with(
        settings.DEFAULT_BUCKET
    )
    storage.from_service_account_json().get_bucket().blob.assert_called_once_with(
        document_1.blob_name
    )
    storage.from_service_account_json().get_bucket().blob().generate_signed_url.assert_called_once_with(
        datetime.timedelta(seconds=60),
        response_disposition='attachment; filename=document.pdf',
    )


@pytest.mark.django_db
def test_download_document_admin(client_admin, order, storage, buyer, admin, seller):
    admin.is_email_verified = True
    admin.save()

    document_1 = mommy.make(
        Document,
        order=order,
        blob_name='documents/123/document.pdf',
        seller={'user_id': seller.id},
    )

    storage.from_service_account_json.return_value.get_bucket.return_value.blob.return_value.generate_signed_url.return_value = (
        'https://example.com'
    )

    response = client_admin.get(
        f'/orders/{order.id}/documents/{document_1.id}/download'
    )

    assert response.json() == {'url': 'https://example.com', 'filename': 'document.pdf'}

    storage.from_service_account_json.assert_called_once_with(mock.ANY)
    storage.from_service_account_json().get_bucket.assert_called_once_with(
        settings.DEFAULT_BUCKET
    )
    storage.from_service_account_json().get_bucket().blob.assert_called_once_with(
        document_1.blob_name
    )
    storage.from_service_account_json().get_bucket().blob().generate_signed_url.assert_called_once_with(
        datetime.timedelta(seconds=60),
        response_disposition='attachment; filename=document.pdf',
    )
