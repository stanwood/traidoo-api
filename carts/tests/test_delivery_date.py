import datetime

import pytest
from django.conf import settings
from django.utils import timezone
from model_bakery import baker

from carts.models import CartItem
from items.models import Item


@pytest.mark.django_db
def test_delivery_date(buyer, client_buyer, traidoo_region):
    cart = baker.make_recipe("carts.cart", user=buyer)
    assert not cart.earliest_delivery_date

    delivery_date = (
        datetime.datetime.now()
        + datetime.timedelta(days=(settings.EARLIEST_DELIVERY_DATE_DAYS_RANGE[0] + 2))
    ).strftime("%Y-%m-%d")

    response = client_buyer.post("/cart/delivery", {"date": delivery_date})
    assert response.status_code == 204

    cart.refresh_from_db()
    assert cart.earliest_delivery_date.strftime("%Y-%m-%d") == delivery_date


@pytest.mark.django_db
def test_delivery_date_not_in_the_future(buyer, client_buyer, traidoo_region):
    cart = baker.make_recipe("carts.cart", user=buyer)
    assert not cart.earliest_delivery_date

    response = client_buyer.post(
        "/cart/delivery",
        {
            "date": (
                datetime.datetime.now()
                + datetime.timedelta(
                    days=(settings.EARLIEST_DELIVERY_DATE_DAYS_RANGE[0] - 1)
                )
            ).strftime("%Y-%m-%d")
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "date": {
            "earliestDeliveryDate": {
                "message": "Date must be in the future.",
                "code": "invalid",
            }
        }
    }

    cart.refresh_from_db()
    assert not cart.earliest_delivery_date


@pytest.mark.django_db
def test_delivery_date_is_too_far_away(buyer, client_buyer, traidoo_region):
    cart = baker.make_recipe("carts.cart", user=buyer)
    assert not cart.earliest_delivery_date

    response = client_buyer.post(
        "/cart/delivery",
        {
            "date": (
                datetime.datetime.now()
                + datetime.timedelta(
                    days=(settings.EARLIEST_DELIVERY_DATE_DAYS_RANGE[1] + 1)
                )
            ).strftime("%Y-%m-%d")
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "date": {
            "earliestDeliveryDate": {
                "message": "Cannot exceed 14 days.",
                "code": "invalid",
            }
        }
    }

    cart.refresh_from_db()
    assert not cart.earliest_delivery_date
