import pytest
from model_bakery import baker

from documents.models import Document
from documents.utils.document_types import get_seller_document_types

from .helpers import create_documents


@pytest.mark.django_db
def test_get_seller_orders_as_anonymous(api_client):
    response = api_client.get("/orders/sales")
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_seller_orders_as_buyer(api_client, buyer_group):
    buyer = baker.make("users.user", groups=[buyer_group])
    api_client.force_authenticate(user=buyer)
    response = api_client.get("/orders/sales")
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_seller_orders(
    api_client, buyer_group, seller_group, traidoo_region,
):
    _, seller, order, documents = create_documents(
        buyer_group, seller_group, traidoo_region, False
    )

    api_client.force_authenticate(user=seller)
    response = api_client.get("/orders/sales")

    json_response = response.json()
    assert json_response["count"] == 1
    assert not json_response["next"]
    assert not json_response["previous"]

    result = json_response["results"][0]
    assert result["id"] == order.id
    assert result["totalPrice"] == 151.02
    assert result["createdAt"] == order.created_at.isoformat().replace("+00:00", "Z")

    seller_document_types = get_seller_document_types()

    assert len(result["documents"]) == len(seller_document_types) == 3

    for document in seller_document_types:
        assert {"documentType": document, "id": documents[document].id,} in result[
            "documents"
        ]
