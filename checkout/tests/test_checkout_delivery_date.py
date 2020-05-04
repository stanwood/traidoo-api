import datetime

import pytest

pytestmark = pytest.mark.django_db


def test_checkout_incorrect_earliest_delivery_date(
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

    cart.earliest_delivery_date = datetime.datetime.now().date()
    cart.save()

    response = client_buyer.post("/checkout")
    assert response.status_code == 400
    assert response.json() == {
        "earliestDeliveryDate": {
            "message": "Date must be in the future.",
            "code": "invalid",
        }
    }
