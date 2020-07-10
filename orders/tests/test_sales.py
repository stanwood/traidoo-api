import pytest
from model_bakery import baker

from documents.models import Document

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
        buyer_group, seller_group, traidoo_region
    )

    api_client.force_authenticate(user=seller)
    response = api_client.get("/orders/sales")

    json_response = response.json()
    assert json_response["count"] == 1
    assert not json_response["next"]
    assert not json_response["previous"]

    result = json_response["results"][0]
    assert result["id"] == order.id
    assert result['buyer'] == {
        'id': order.buyer.id,
        'firstName': order.buyer.first_name,
        'lastName': order.buyer.last_name,
        'companyName': order.buyer.company_name,
    }
    assert result["totalPrice"] == 50.35
    assert result["createdAt"] == order.created_at.isoformat().replace("+00:00", "Z")

    assert len(result["documents"]) == len(documents) - 1

    for document_type, document in documents.items():
        if (
            document.seller["user_id"] == seller.id
            or document.buyer["user_id"] == seller.id
        ):
            assert {"documentType": document_type, "id": document.id,} in result[
                "documents"
            ]
