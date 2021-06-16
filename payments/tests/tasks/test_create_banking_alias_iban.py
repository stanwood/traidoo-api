from unittest import mock

import pytest
from model_bakery import baker


@pytest.mark.django_db
@mock.patch("payments.client.client.MangopayClient.post")
def test_create_banking_alias_iban(
    mocked_post, client_anonymous, send_task, traidoo_region
):
    wallet_id = "wallet-1"
    user = baker.make_recipe("users.user", mangopay_user_id=123, region=traidoo_region)

    mocked_post.side_effect = [
        {
            "IBAN": "FR7618829754160173622224251",
            "BIC": "CMBRFR2BCME",
            "Id": "234514543",
            "OwnerName": "Test Test",
        },
    ]

    client_anonymous.post(
        "/mangopay/tasks/create-banking-alias-iban",
        {"user_id": user.id, "wallet_id": wallet_id},
        **{"HTTP_X_APPENGINE_QUEUENAME": "queue"},
    )

    assert mocked_post.call_args_list == [
        mock.call(
            "/wallets/wallet-1/bankingaliases/iban",
            {
                "CreditedUserId": str(user.mangopay_user_id),
                "OwnerName": user.company_name,
                "Country": "FR",
            },
        ),
    ]
