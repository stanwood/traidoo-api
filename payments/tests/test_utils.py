import pytest

from payments.utils import lookup_user_type, lookup_legal_person_type

pytestmark = pytest.mark.django_db


def test_account_type_lookup():
    assert lookup_user_type("gbr") == "legal"
    assert lookup_legal_person_type("gbr") == "SOLETRADER"

    assert lookup_user_type("Landwirtschaftliche GbR") == "legal"
    assert (
        lookup_legal_person_type("Landwirtschaftliche GbR")
        == "SOLETRADER"
    )
