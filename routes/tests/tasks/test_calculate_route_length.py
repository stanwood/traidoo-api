from unittest import mock

import pytest
from model_mommy import mommy

from ...models import Route


@pytest.mark.django_db
@mock.patch('routes.models.calculate_route_length')
def test_tasks_calculate_route_length(
    calculate_route_length_mock, faker, send_task, client_anonymous
):
    calculate_route_length_mock.return_value = 123
    origin = faker.address()
    destination = faker.address()
    waypoints = [faker.address(), faker.address()]
    route = mommy.make(
        Route, origin=origin, destination=destination, waypoints=waypoints
    )

    assert route.length == 0

    response = client_anonymous.post(
        f'/routes/{route.id}/calculate_route_length',
        **{'HTTP_X_APPENGINE_QUEUENAME': 'queue'},
    )

    assert response.status_code == 200

    route.refresh_from_db()
    assert route.length == 123

