from unittest import mock

import pytest
from ..models import Route
from model_mommy import mommy


@pytest.mark.django_db
def test_delete_route(seller, client_seller, send_task):
    route = mommy.make(Route, user=seller)

    response = client_seller.delete(f'/routes/{route.id}')

    response.status_code == 201

    with pytest.raises(Route.DoesNotExist):
        route.refresh_from_db()

    assert not (
        mock.call(
            f'/routes/{route.id}/calculate_route_length',
            http_method='POST',
            queue_name='routes',
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
def test_delete_someone_else_route(buyer, client_seller, send_task):
    route = mommy.make(Route, user=buyer)

    response = client_seller.delete(f'/routes/{route.id}')

    response.status_code == 403

    route.refresh_from_db()

    assert not (
        mock.call(
            f'/routes/{route.id}/calculate_route_length',
            http_method='POST',
            queue_name='routes',
        )
        in send_task.call_args_list
    )
