import itertools
from decimal import Decimal

import pytest

from core.calculators.order_calculator import OrderCalculatorMixin

pytestmark = pytest.mark.django_db


def test_item_price_calculation():
    item = OrderCalculatorMixin.Item(amount=3, price=10, vat=20, count=2, seller=1)

    price_value = item.value
    assert price_value.netto == 3 * 10 * 2
    assert price_value.brutto == 3 * 10 * 2 * 1.2
    assert price_value.vat == 3 * 10 * 2 * 0.2


def test_total_calculation_error():
    items = [
        OrderCalculatorMixin.Item(
            vat=7, price=9.48, amount=1, count=1.97, seller="traidoo"
        ),
        OrderCalculatorMixin.Item(
            vat=7, price=1.79, amount=5, count=1.83, seller="biogemuse"
        ),
    ]

    gross = 0

    items = sorted(items, key=lambda l: l.seller)

    for seller_id, items in itertools.groupby(items, lambda item: item.seller):
        gross += OrderCalculatorMixin.calculate_gross_value_of_items(items)

    assert float(gross) == float(Decimal("37.52"))


def test_total_calculation_sort_by_vat_rate():

    items = [
        OrderCalculatorMixin.Item(
            vat=7, price=13.5, amount=1, count=1, seller="traidoo"
        ),
        OrderCalculatorMixin.Item(
            vat=19, price=19.3, amount=1, count=1, seller="traidoo"
        ),
        OrderCalculatorMixin.Item(
            vat=7, price=119.7, amount=1, count=1, seller="traidoo"
        ),
    ]

    mixin = OrderCalculatorMixin()
    assert mixin.calculate_gross_value_of_items(items) == Decimal("165.49")
