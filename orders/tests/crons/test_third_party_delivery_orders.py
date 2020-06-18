import datetime
from unittest import mock

import pytest
from django.conf import settings
from model_bakery import baker

from orders.models import Order

pytestmark = pytest.mark.django_db


def test_send_documents_task_for_third_party_orders(
    client_anonymous, send_task, settings, traidoo_region
):
    settings.FEATURES['routes'] = True

    order_1 = baker.make(Order, processed=False)
    order_2 = baker.make(Order, processed=True)

    response = client_anonymous.get(
        '/orders/crons/third-party-delivery-orders', **{'HTTP_X_APPENGINE_CRON': True}
    )

    assert response.status_code == 204

    assert (
        mock.call(
            f'/documents/queue/{order_1.id}/all',
            queue_name='documents',
            headers={'Region': order_1.region.slug},
            http_method='POST',
            schedule_time=60,
        )
        in send_task.call_args_list
    )
    assert not (
        mock.call(
            f'/documents/queue/{order_2.id}/all',
            queue_name='documents',
            headers={'Region': order_2.region.slug},
            http_method='POST',
            schedule_time=60,
        )
        in send_task.call_args_list
    )
