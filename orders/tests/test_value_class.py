import pytest

from core.calculators.value import Value

pytestmark = pytest.mark.django_db


def test_sum_values_without_including_rounding_error():

    total = sum([Value(7.8, 7), Value(0.97, 7)])

    assert total.vat == 0.62
    assert total.brutto == 9.39

    total = Value(20.75, 7)
    assert total.brutto == 22.2
    assert total.vat == 1.45

    # Test case when sum of values fails
    # total = sum(
    #     [Value(1.7, 7), Value(13.95, 7), Value(1.7, 7), Value(1.7, 7), Value(1.7, 7)]
    # )
    #
    # assert total.brutto == 22.2
    # assert total.vat == 1.45
