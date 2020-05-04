import datetime

import pytest

pytestmark = pytest.mark.django_db


def test_checkout_optional_delivery_address(
    client_buyer,
    cart,
    buyer,
    product,
    delivery_address,
    delivery_options,
    send_task,
    logistics_user,
    platform_user,
):
    product.price = 60
    product.save()

    cart.earliest_delivery_date = (
        datetime.datetime.now() + datetime.timedelta(days=2)
    ).date()
    cart.delivery_address = None
    cart.save()

    response = client_buyer.post("/checkout")
    assert response.status_code == 400
    assert response.json() == "Delivery address is required."
