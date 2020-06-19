import pytest
from model_bakery import baker

from ..models import DeliveryAddress

pytestmark = pytest.mark.django_db


def test_delivery_address_as_str():
    company_name = 'Company Name'
    zip_code = 123
    city = 'City'
    street = 'Street'

    delivery_address = baker.make(
        DeliveryAddress,
        company_name=company_name,
        zip=zip_code,
        city=city,
        street=street,
    )
    assert delivery_address.as_str() == f'{company_name}, {street}, {zip_code}, {city}'
