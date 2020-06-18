from unittest import mock

import pytest
from model_bakery import baker

from ...models import Detour

pytestmark = pytest.mark.django_db


@mock.patch('jobs.tasks.create_detours.calculate_route_length')
def test_create_detours_for_route(
    calculate_route_length_mock, client_anonymous, settings
):
    settings.FEATURES['routes'] = True

    default_route_length = 1200
    calculate_route_length_mock.return_value = default_route_length

    route = baker.make('routes.Route')

    product_1 = baker.make('products.Product', third_party_delivery=False)
    order_1 = baker.make('orders.Order', processed=False)
    order_item_1 = baker.make_recipe(
        'orders.orderitem', order=order_1, product=product_1
    )

    product_2 = baker.make('products.Product', third_party_delivery=True)
    order_2 = baker.make('orders.Order', processed=True)
    order_item_2 = baker.make(
        'orders.OrderItem', order=order_2, job=None, product=product_2
    )

    seller_1 = baker.make_recipe('users.user')
    product_3 = baker.make(
        'products.Product', third_party_delivery=True, seller=seller_1
    )
    order_3 = baker.make('orders.Order', processed=False)
    delivery_address_1 = baker.make_recipe('delivery_addresses.delivery_address')
    order_item_3 = baker.make(
        'orders.OrderItem',
        order=order_3,
        product=product_3,
        delivery_address=delivery_address_1,
    )
    job_1 = baker.make('jobs.Job', order_item=order_item_3, user=None)

    seller_2 = baker.make_recipe('users.user')
    product_4 = baker.make(
        'products.Product', third_party_delivery=True, seller=seller_2
    )
    order_4 = baker.make('orders.Order', processed=False)
    delivery_address_2 = baker.make_recipe('delivery_addresses.delivery_address')
    order_item_4 = baker.make(
        'orders.OrderItem',
        order=order_4,
        product=product_4,
        delivery_address=delivery_address_2,
    )
    user = baker.make('users.User')
    job_2 = baker.make('jobs.Job', order_item=order_item_4, user=user)

    assert not Detour.objects.first()

    response = client_anonymous.post(
        f'/detours/create/{route.id}', **{'HTTP_X_APPENGINE_QUEUENAME': 'queue'}
    )

    assert response.status_code == 200

    assert Detour.objects.count() == 2

    detour_1 = Detour.objects.filter(job=job_1).first()
    assert detour_1.route == route
    assert detour_1.length == default_route_length
    detour_2 = Detour.objects.filter(job=job_2).first()
    assert detour_2.route == route
    assert detour_2.length == default_route_length
