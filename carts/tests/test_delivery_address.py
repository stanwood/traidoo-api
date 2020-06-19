import datetime

import pytest
from model_bakery import baker

from carts.models import CartItem
from items.models import Item


@pytest.mark.django_db
def test_delivery_address(buyer, client_buyer, traidoo_region, delivery_address):
    cart = baker.make_recipe("carts.cart", user=buyer)
    assert not cart.delivery_address

    response = client_buyer.post(
        "/cart/deliveryAddress", {"deliveryAddress": delivery_address.id}
    )
    assert response.status_code == 204

    cart.refresh_from_db()
    assert cart.delivery_address.id == delivery_address.id


@pytest.mark.django_db
def test_delivery_address_when_cart_does_not_exist(buyer, client_buyer, traidoo_region):
    response = client_buyer.post(
        "/cart/deliveryAddress", {"deliveryAddress": 123123123}
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_delivery_address_when_address_does_not_exist(
    buyer, client_buyer, traidoo_region
):
    cart = baker.make_recipe("carts.cart", user=buyer)
    assert not cart.delivery_address

    response = client_buyer.post(
        "/cart/deliveryAddress", {"deliveryAddress": 123123123}
    )
    assert response.status_code == 404

    cart.refresh_from_db()
    assert not cart.delivery_address
