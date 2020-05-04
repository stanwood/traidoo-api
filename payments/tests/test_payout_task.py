from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_mommy import mommy

from orders.models import Order

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def mangopay(mangopay):
    mangopay.return_value.get_user_wallets.return_value = [
        {
            "Currency": "EUR",
            "Description": "Default",
            "Balance": {"Amount": 10000},
            "Id": "wallet-1",
        }
    ]
    mangopay.return_value.get_bank_accounts.return_value = [{"Id": "bank-account-1"}]
    yield mangopay


def test_do_not_try_create_bank_account_when_format_is_wrong(
    mangopay, api_client, traidoo_region
):
    mommy.make(User, mangopay_user_id="999", iban="-")
    mommy.make(Order, id=99)
    mangopay.return_value.get_bank_accounts.return_value = []

    api_client.post(
        reverse("payouts-user", kwargs={"mangopay_user_id": "999"}),
        data={"amount": "100", "order_id": "99"},
        HTTP_X_APPENGINE_CRON="True",
    )

    mangopay.post.assert_not_called()


def test_create_payout_for_order(mangopay, api_client, central_platform_user):
    mommy.make(Order, id=99)
    mommy.make(User, mangopay_user_id="999")

    api_client.post(
        reverse("payouts-user", kwargs={"mangopay_user_id": "999"}),
        data={"amount": 10, "order_id": "99"},
        HTTP_X_APPENGINE_CRON="True",
    )

    mangopay.return_value.get_user_wallets.assert_called_with("999")
    mangopay.return_value.get_bank_accounts.assert_called_with("999")
    mangopay.return_value.create_pay_out.assert_called_with(
        author_id=central_platform_user.mangopay_user_id,
        amount=1000,
        bank_account_id="bank-account-1",
        wallet_id="wallet-1",
        wire_reference="order #99",
    )
