import pytest

pytestmark = pytest.mark.django_db


def test_item_calculations(order_items):

    assert order_items[0].price.netto == 95.4
    assert order_items[0].price_gross == 113.53
    assert order_items[0].container_deposit.netto == 3.2
    assert order_items[0]._delivery_fee().netto == 15.81
