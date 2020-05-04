import datetime

import pytest
from dictdiffer import diff
from django.utils import timezone
from freezegun import freeze_time
from model_mommy import mommy


def _create_items(delta_days=0, price=1, order_status=1):
    products = mommy.make('products.Product', price=price, _quantity=2)

    created_at = timezone.now() - datetime.timedelta(days=delta_days)

    with freeze_time(created_at):
        order = mommy.make('orders.Order', status=order_status)
        mommy.make('orders.OrderItem', order=order, product=products[0], quantity=2)
        mommy.make('orders.OrderItem', order=order, product=products[1], quantity=1)


@pytest.mark.django_db
def test_admin_stats(client_admin):
    _create_items()
    _create_items(1, order_status=2)
    _create_items(2, order_status=0)
    _create_items(4)
    _create_items(14, 2.1, order_status=2)
    _create_items(34, 2.1)

    response = client_admin.get(f'/items/stats/admin')

    assert not list(
        diff(
            response.json(),
            {
                'today': {'value': 3.0, 'change': 0, 'previous': 3.0},
                '7': {'value': 9.0, 'change': 42.9, 'previous': 6.3},
                '30': {'value': 15.3, 'change': 142.9, 'previous': 6.3},
            },
        )
    )
