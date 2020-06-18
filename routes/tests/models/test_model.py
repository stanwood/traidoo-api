from unittest import mock

import pytest
from model_bakery import baker

from ...models import Route


@pytest.mark.django_db
@mock.patch('routes.models.calculate_route_length')
def test_route_model_calculate_route_length(
    calculate_route_length_mock, faker, send_task
):
    calculate_route_length_mock.return_value = 123
    origin = faker.address()
    destination = faker.address()
    waypoints = [faker.address(), faker.address()]
    route = baker.make(
        Route, origin=origin, destination=destination, waypoints=waypoints
    )

    route.calculate_route_length()

    calculate_route_length_mock.assert_called_once_with(origin, destination, waypoints)
    route.length = 123

    assert not (
        mock.call(
            f'/routes/{route.id}/calculate_route_length',
            http_method='POST',
            queue_name='routes',
        )
        in send_task.call_args_list
    )
