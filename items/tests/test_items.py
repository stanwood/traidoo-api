import datetime

import pytest
from django.utils import timezone


YMD_FORMAT = '%Y-%m-%d'


@pytest.mark.django_db(transaction=True)
def test_unique_product_and_delivery_date(client_seller, product):
    delivery_date = (timezone.now().date() + datetime.timedelta(days=1)).strftime(
        YMD_FORMAT
    )

    response = client_seller.post(
        '/items',
        {'latestDeliveryDate': delivery_date, 'productId': product.id, 'quantity': 222},
    )

    assert response.status_code == 201

    response = client_seller.post(
        '/items',
        {'latestDeliveryDate': delivery_date, 'productId': product.id, 'quantity': 222},
    )

    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_do_not_allow_to_add_ite_with_today_as_delivery_date(client_seller, product):

    response = client_seller.post(
        '/items',
        {
            'latestDeliveryDate': timezone.now().date().strftime(YMD_FORMAT),
            'productId': product.id,
            'quantity': 222,
        },
    )

    assert response.status_code == 400
    assert response.json()['nonFieldErrors'] == [
        {
            'message': f"latest_delivery_date must greater than {timezone.now().date().strftime(YMD_FORMAT)}",
            'code': 'invalid',
        }
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("valid_from", [
    ((timezone.now().date() + datetime.timedelta(days=5)).strftime(YMD_FORMAT)),
    (None)
])
def test_valid_from_is_optional_field(client_seller, product, valid_from):
    delivery_date = (
        timezone.now().date() + datetime.timedelta(days=10)
    ).strftime(YMD_FORMAT)

    payload = {
        'latestDeliveryDate': delivery_date,
        'productId': product.id,
        'quantity': 222,
    }

    if valid_from:
        payload['valid_from'] = valid_from

    response = client_seller.post(
        '/items',
        payload,
    )
    parsed_response = response.json()

    assert response.status_code == 201
    assert parsed_response['validFrom'] == valid_from
