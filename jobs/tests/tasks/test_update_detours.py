from unittest import mock

import pytest
from model_bakery import baker

pytestmark = pytest.mark.django_db


@mock.patch("jobs.tasks.update_detours.calculate_route_length")
def test_update_detours_for_route(
    calculate_route_length_mock, client_anonymous, settings
):
    settings.FEATURES["routes"] = True

    default_route_length = 1200
    calculate_route_length_mock.return_value = default_route_length

    seller_1 = baker.make_recipe("users.user")
    product_1 = baker.make("products.Product", seller=seller_1)
    order_1 = baker.make("orders.Order")
    delivery_address_1 = baker.make_recipe("delivery_addresses.delivery_address")
    order_item_1 = baker.make(
        "orders.OrderItem",
        order=order_1,
        product=product_1,
        delivery_address=delivery_address_1,
    )
    user = baker.make("users.User")
    job_2 = baker.make("jobs.Job", order_item=order_item_1, user=user)
    route_2 = baker.make("routes.Route")
    detour_2 = baker.make("jobs.Detour", route=route_2, length=123, job=job_2)

    response = client_anonymous.post(
        f"/detours/update/{route_2.id}", **{"HTTP_X_APPENGINE_QUEUENAME": "queue"}
    )

    assert response.status_code == 200

    detour_2.refresh_from_db()

    assert detour_2.length == default_route_length
