from unittest import mock

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize('url', ['/users/', '/auth/users/'])
def test_change_group_as_user(
    url, seller, buyer, client_seller, seller_group, buyer_group
):
    assert list(seller.groups.values_list('name', flat=True)) == ['seller']

    response = client_seller.patch(f'{url}{seller.id}', {'groups': ['seller', 'buyer']})

    assert response.status_code == 200

    seller.refresh_from_db()
    assert list(seller.groups.values_list('name', flat=True)) == ['seller']
