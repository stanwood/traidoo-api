from unittest import mock

import pytest
from model_mommy import mommy


@pytest.mark.django_db
@mock.patch("payments.client.client.MangopayClient.post")
def test_create_wallet(mocked_post, client_anonymous, send_task, traidoo_region):
    user = mommy.make_recipe("users.user", mangopay_user_id=123, region=traidoo_region)
    wallet_id = "wallet-1"

    mocked_post.side_effect = [
        {"Id": wallet_id, "Currency": "EUR", "Description": "Default"},
    ]

    client_anonymous.post(
        "/mangopay/tasks/create-wallet",
        {"user_id": user.id},
        **{"HTTP_X_APPENGINE_QUEUENAME": "queue"},
    )

    assert mocked_post.call_args_list == [
        mock.call(
            "/wallets",
            {
                "Owners": [str(user.mangopay_user_id)],
                "Description": "Default",
                "Currency": "EUR",
            },
        ),
    ]

    send_task.assert_called_once_with(
        f"/mangopay/tasks/create-banking-alias-iban",
        payload={"user_id": user.id, "wallet_id": wallet_id},
        http_method="POST",
        queue_name="mangopay-banking-alias-iban",
        schedule_time=5,
        headers={"Region": traidoo_region.slug},
    )
