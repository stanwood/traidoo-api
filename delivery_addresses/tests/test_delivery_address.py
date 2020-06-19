import random

import pytest
from model_bakery import baker

from delivery_addresses.models import DeliveryAddress

pytestmark = pytest.mark.django_db


def test_get_own_delivery_addresses(client_seller, seller, buyer):
    baker.make_recipe("delivery_addresses.delivery_address", user=buyer)
    address_1, address_2 = baker.make_recipe(
        "delivery_addresses.delivery_address", user=seller, _quantity=2
    )

    response = client_seller.get("/delivery_addresses")

    assert response.json() == [
        {
            "city": address_1.city,
            "companyName": address_1.company_name,
            "id": address_1.id,
            "street": address_1.street,
            "zip": address_1.zip,
        },
        {
            "city": address_2.city,
            "companyName": address_2.company_name,
            "id": address_2.id,
            "street": address_2.street,
            "zip": address_2.zip,
        },
    ]


def test_get_own_delivery_address(client_seller, seller):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=seller)

    response = client_seller.get(f"/delivery_addresses/{address.id}")

    assert response.json() == {
        "city": address.city,
        "companyName": address.company_name,
        "id": address.id,
        "street": address.street,
        "zip": address.zip,
    }


def test_get_someone_else_delivery_address(client_seller, buyer):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=buyer)

    response = client_seller.get(f"/delivery_addresses/{address.id}")
    assert response.status_code == 404


def test_add_delivery_address(client_seller, seller, faker):
    data = {
        "city": faker.city(),
        "companyName": faker.company(),
        "street": faker.street_address(),
        "zip": faker.zipcode(),
    }

    response = client_seller.post("/delivery_addresses", data)

    assert response.json() == {
        "id": DeliveryAddress.objects.first().id,
        "companyName": data["companyName"],
        "street": data["street"],
        "zip": data["zip"],
        "city": data["city"],
    }


def test_edit_delivery_address(client_seller, seller, faker):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=seller)

    data = {
        "city": faker.city(),
        "companyName": faker.company(),
        "street": faker.street_address(),
        "zip": faker.zipcode(),
    }

    response = client_seller.put(f"/delivery_addresses/{address.id}", data)

    assert response.json() == {
        "id": address.id,
        "companyName": data["companyName"],
        "street": data["street"],
        "zip": data["zip"],
        "city": data["city"],
    }

    address.refresh_from_db()

    assert address.city == data["city"]
    assert address.company_name == data["companyName"]
    assert address.street == data["street"]
    assert address.zip == data["zip"]


def test_edit_someone_else_delivery_address(client_buyer, seller, buyer, faker):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=seller)

    data = {
        "city": faker.city(),
        "companyName": faker.company(),
        "street": faker.street_address(),
        "zip": faker.zipcode(),
    }

    response = client_buyer.put(f"/delivery_addresses/{address.id}", data)
    assert response.status_code == 404


def test_partially_edit_delivery_address(client_seller, seller, faker):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=seller)

    data = {
        "city": faker.city(),
        "companyName": faker.company(),
        "street": faker.street_address(),
        "zip": faker.zipcode(),
    }

    for key, value in data.items():
        response = client_seller.patch(f"/delivery_addresses/{address.id}", data)
        assert response.json()[key] == value


def test_partially_edit_someone_else_delivery_address(
    client_buyer, seller, buyer, faker
):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=seller)
    response = client_buyer.patch(
        f"/delivery_addresses/{address.id}", {"city": faker.city()}
    )
    assert response.status_code == 404


def test_delete_delivery_address(client_seller, seller, faker):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=seller)
    response = client_seller.delete(f"/delivery_addresses/{address.id}")

    with pytest.raises(DeliveryAddress.DoesNotExist):
        address.refresh_from_db()


def test_delete_someone_else_delivery_address(client_seller, buyer, faker):
    address = baker.make_recipe("delivery_addresses.delivery_address", user=buyer)
    response = client_seller.delete(f"/delivery_addresses/{address.id}")
    assert response.status_code == 404
    assert not address.refresh_from_db()
