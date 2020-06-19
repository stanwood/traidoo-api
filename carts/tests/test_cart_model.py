from decimal import Decimal

import django
import pytest
from model_bakery import baker

from carts.models import Cart, CartItem


@pytest.fixture
def cart(buyer):
    yield baker.make(Cart, user=buyer)


@pytest.fixture
def cart_items(cart, products):
    yield [
        baker.make(CartItem, cart=cart, product=products[0], quantity=1),
        baker.make(CartItem, cart=cart, product=products[1], quantity=2),
    ]


@pytest.mark.django_db
def test_total_value(cart, cart_items, products):
    cart = Cart.objects.first()
    assert Decimal(str(cart.price)) == Decimal(
        sum(
            [
                products[0].price * products[0].amount * cart_items[0].quantity,
                products[1].price * products[1].amount * cart_items[1].quantity,
            ]
        )
    ).quantize(Decimal(".01"), "ROUND_HALF_UP")


@pytest.mark.django_db
def test_delete_delivery_address_assigned_to_cart(cart, delivery_address):
    cart.delivery_address = delivery_address
    cart.save()

    with pytest.raises(django.db.models.deletion.ProtectedError):
        delivery_address.delete()


@pytest.mark.django_db
def test_delete_cart_with_delivery_address(cart, delivery_address):
    cart.delivery_address = delivery_address
    cart.save()

    cart.delete()

    with pytest.raises(Cart.DoesNotExist):
        cart.refresh_from_db()

    assert not delivery_address.refresh_from_db()
