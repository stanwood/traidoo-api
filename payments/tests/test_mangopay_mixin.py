from unittest import mock

import pytest

from payments.mixins import MangopayMixin


@pytest.fixture
def mangopay_client():
    with mock.patch("payments.mixins.MangopayClient") as mangopay:
        yield mangopay.return_value


def test_create_wallet_if_missing(mangopay_client):
    mangopay_mixin = MangopayMixin()
    mangopay_client.get_user_wallets.return_value = []
    mangopay_mixin.get_user_wallet("test-user-1")
    mangopay_client.create_wallet.assert_called_with("test-user-1")
