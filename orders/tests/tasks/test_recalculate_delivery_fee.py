import pytest
from model_bakery import baker

pytestmark = pytest.mark.django_db


def test_recalculate_delivery_fee(client_anonymous, send_task, traidoo_region):
    response = client_anonymous.get(
        '/order-items/tasks/recalculate-delivery-fee?token=12l31jb31283kjhqweb'
    )

    assert response.status_code == 204

    send_task.assert_called_with(
        '/order-items/tasks/recalculate-delivery-fee?token=12l31jb31283kjhqweb',
        http_method='POST',
        headers={'Region': traidoo_region.slug}
    )


def test_recalculate_delivery_fee_incorrect_token(client_anonymous, send_task):
    response = client_anonymous.get(
        '/order-items/tasks/recalculate-delivery-fee?token=123'
    )

    assert response.status_code == 403

    send_task.assert_not_called()


def test_recalculate_delivery_fee_post_incorrect_token(client_anonymous, send_task):
    response = client_anonymous.post(
        '/order-items/tasks/recalculate-delivery-fee?token=123'
    )

    assert response.status_code == 403
