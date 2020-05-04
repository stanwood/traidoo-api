import datetime

import pytest
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from model_mommy import mommy

from carts.models import Cart, CartItem
from items.models import Item


@pytest.fixture
def cart(buyer):
    yield mommy.make(Cart, user=buyer)


@pytest.fixture
def cart_items(cart, products):
    yield [
        mommy.make(CartItem, cart=cart, product=products[0], quantity=1),
        mommy.make(CartItem, cart=cart, product=products[1], quantity=2),
    ]


@pytest.mark.django_db
def test_delete_inactive_carts(
    client_anonymous, cart, cart_items, django_assert_num_queries
):
    assert (
        Item.objects.filter(
            product=cart_items[0].product,
            latest_delivery_date=cart_items[0].latest_delivery_date,
        ).first()
        == None
    )
    assert (
        Item.objects.filter(
            product=cart_items[1].product,
            latest_delivery_date=cart_items[1].latest_delivery_date,
        ).first()
        == None
    )

    updated_at = timezone.now() + datetime.timedelta(minutes=settings.CART_LIFESPAN + 1)

    with django_assert_num_queries(12):
        with freeze_time(updated_at):
            client_anonymous.get(
                "/carts/cron/delete-inactive-carts", **{"HTTP_X_APPENGINE_CRON": True}
            )

    assert (
        Item.objects.filter(
            product=cart_items[0].product,
            latest_delivery_date=cart_items[0].latest_delivery_date,
        )
        .first()
        .quantity
        == cart_items[0].quantity
    )

    assert (
        Item.objects.filter(
            product=cart_items[1].product,
            latest_delivery_date=cart_items[1].latest_delivery_date,
        )
        .first()
        .quantity
        == cart_items[1].quantity
    )

    assert not Cart.objects.all()
    assert not CartItem.objects.all()
