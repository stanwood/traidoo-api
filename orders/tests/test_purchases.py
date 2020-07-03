import pytest
from model_bakery import baker

from documents.models import Document
from documents.utils.document_types import get_buyer_document_types

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
    assert response.status_code == 403


@pytest.mark.parametrize(
    "cooperative_member,number_of_documents", [(True, 5), (False, 4)],
)
@pytest.mark.django_db
def test_get_buyer_orders(
    cooperative_member,
    number_of_documents,
    api_client,
    buyer_group,
    seller_group,
    traidoo_region,
):
    buyer, _, order, documents = create_documents(
        buyer_group, seller_group, traidoo_region, cooperative_member=cooperative_member
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

    buyer_document_types = get_buyer_document_types(buyer)

    assert len(result["documents"]) == len(buyer_document_types) == number_of_documents

    for document in buyer_document_types:
        assert {"documentType": document, "id": documents[document].id,} in result[
            "documents"
        ]
