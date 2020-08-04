import pytest
from model_bakery import baker

from documents.models import Document

from .helpers import create_documents


@pytest.mark.django_db
def test_get_buyer_orders_as_anonymous(api_client):
    response = api_client.get("/orders/purchases")
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_buyer_orders_as_seller(api_client, seller_group):
    seller = baker.make("users.user", groups=[seller_group])
    api_client.force_authenticate(user=seller)
    response = api_client.get("/orders/purchases")
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_buyer_orders(
    api_client, buyer_group, seller_group, traidoo_region,
):
    buyer, _, order, documents = create_documents(
        buyer_group, seller_group, traidoo_region
    )

    api_client.force_authenticate(user=buyer)
    response = api_client.get("/orders/purchases")

    json_response = response.json()
    assert json_response["count"] == 1
    assert not json_response["next"]
    assert not json_response["previous"]

    result = json_response["results"][0]
    assert result["id"] == order.id
    assert result["totalPrice"] == order.total_price
    assert result["createdAt"] == order.created_at.isoformat().replace("+00:00", "Z")

    assert len(result["documents"]) == len(documents) - 1

    for document_type, document in documents.items():
        if (
            document.seller["user_id"] == buyer.id
            or document.buyer["user_id"] == buyer.id
        ):
            assert {"documentType": document_type, "id": document.id,} in result[
                "documents"
            ]
