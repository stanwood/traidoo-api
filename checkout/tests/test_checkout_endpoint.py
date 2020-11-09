from unittest import mock

import pytest

from core.currencies import CURRENT_CURRENCY_CODE
from orders.models import Order

pytestmark = pytest.mark.django_db


def test_order_value_below_min(client_buyer, cart, buyer, products):
    products[0].price = 1
    products[0].save()
    products[1].price = 1
    products[1].save()

    response = client_buyer.post("/checkout")
    assert response.status_code == 400

    assert (
        response.data
        == f"Order must exceed 50.00 {CURRENT_CURRENCY_CODE}. This cart net value is {cart.total}"
    )


def test_order_value_below_min_seller(client_seller, cart, seller, products):
    products[0].price = 1
    products[0].save()
    products[1].price = 1
    products[1].save()

    cart.user = seller
    cart.save()

    response = client_seller.post("/checkout")
    assert response.status_code == 400

    assert (
        response.data
        == f"Order must exceed 50.00 {CURRENT_CURRENCY_CODE}. This cart net value is {cart.total}"
    )


def test_do_not_restore_product_items_after_checkout(
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
    cart.items.update(delivery_option=2)

    product.price = 60
    product.save()

    assert product.items.count() == 0

    response = client_buyer.post("/checkout")
    assert response.status_code == 200

    assert product.items.count() == 0


def test_checkout_3rd_party_delivery_enabled_and_order_has_3rd_party_delivery_product(
    client_buyer,
    cart,
    buyer,
    product,
    delivery_address,
    delivery_options,
    send_task,
    logistics_user,
    settings,
    platform_user,
):
    cart.items.update(delivery_option=2)

    settings.FEATURES["routes"] = True

    product.price = 60
    product.third_party_delivery = True
    product.save()

    response = client_buyer.post("/checkout")
    assert response.status_code == 200

    orders = Order.objects.all()

    assert (
        mock.call(
            f"/documents/queue/{orders[0].id}/all",
            queue_name="documents",
            http_method="POST",
            schedule_time=60,
        )
        not in send_task.call_args_list
    )


def test_checkout_3rd_party_delivery_enabled_but_order_has_no_3rd_party_delivery_product(
    client_buyer,
    cart,
    buyer,
    product,
    delivery_address,
    delivery_options,
    send_task,
    logistics_user,
    settings,
    platform_user,
    traidoo_region,
):
    cart.items.update(delivery_option=2)

    settings.FEATURES["routes"] = True

    product.price = 60
    product.third_party_delivery = False
    product.save()

    response = client_buyer.post("/checkout")
    assert response.status_code == 200

    orders = Order.objects.all()

    send_task.assert_called_with(
        f"/documents/queue/{orders[0].id}/all",
        queue_name="documents",
        http_method="POST",
        schedule_time=60,
        headers={"Region": traidoo_region.slug},
    )
