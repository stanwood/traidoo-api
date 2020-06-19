from unittest import mock

import pytest
from ..models import Route
from model_bakery import baker


@pytest.mark.django_db
@mock.patch('routes.models.calculate_route_length')
def test_edit_route(
    calculate_route_length_mock, seller, buyer, client_seller, faker, send_task
):
    calculate_route_length_mock.return_value = 123

    origin = faker.address()
    destination = faker.address()
    waypoints = [faker.address(), faker.address()]
    frequency = [1, 7]

    route_1 = baker.make(Route, user=seller)

    assert route_1.frequency == []
    assert route_1.waypoints == []

    response = client_seller.put(
        f'/routes/{route_1.id}',
        {
            'frequency': frequency,
            'waypoints': waypoints,
            'origin': origin,
            'destination': destination,
        },
    )

    assert response.status_code == 200
    assert response.json()['waypoints'] == waypoints
    assert response.json()['frequency'] == frequency
    assert response.json()['origin'] == origin
    assert response.json()['destination'] == destination
    assert response.json()['length'] == 123
    assert response.json()['createdAt']
    assert response.json()['updatedAt']
    assert response.json()['id']

    route_1.refresh_from_db()

    assert route_1.frequency == frequency
    assert route_1.waypoints == waypoints
    assert route_1.length == 123

    calculate_route_length_mock.assert_called_once()

    assert (
        mock.call(
            f"/detours/update/{response.json()['id']}",
            http_method='POST',
            queue_name='routes',
            schedule_time=60,
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
@mock.patch('routes.models.calculate_route_length')
def test_edit_route_partially(
    calculate_route_length_mock, seller, buyer, client_seller, send_task, faker
):
    waypoints = [faker.address(), faker.address()]

    route_1 = baker.make(Route, user=seller)

    new_length = route_1.length + 100
    calculate_route_length_mock.return_value = new_length
    assert route_1.length != new_length

    assert route_1.frequency == []

    response = client_seller.patch(f'/routes/{route_1.id}', {'waypoints': waypoints})

    assert response.status_code == 200
    assert response.json()['waypoints'] == waypoints
    assert response.json()['length'] == new_length

    route_1.refresh_from_db()

    assert route_1.waypoints == waypoints

    calculate_route_length_mock.assert_called_once()

    assert (
        mock.call(
            f"/detours/update/{response.json()['id']}",
            http_method='POST',
            queue_name='routes',
            schedule_time=60,
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
@mock.patch('routes.models.calculate_route_length')
def test_edit_route_without_updating_points(
    calculate_route_length_mock, seller, buyer, client_seller, faker, send_task
):
    waypoints = [faker.address(), faker.address()]
    frequency = [1, 7]

    route_1 = baker.make(Route, user=seller)

    assert route_1.frequency == []
    assert route_1.waypoints == []

    response = client_seller.patch(f'/routes/{route_1.id}', {'frequency': frequency})

    assert response.status_code == 200
    assert response.json()['waypoints'] == route_1.waypoints
    assert response.json()['frequency'] == frequency
    assert response.json()['origin'] == route_1.origin
    assert response.json()['destination'] == route_1.destination
    assert response.json()['length'] == route_1.length
    assert response.json()['createdAt']
    assert response.json()['updatedAt']
    assert response.json()['id']

    route_1.refresh_from_db()

    assert route_1.frequency == frequency
    assert route_1.waypoints == route_1.waypoints

    calculate_route_length_mock.assert_not_called()

    assert not (
        mock.call(
            f"/detours/update/{response.json()['id']}",
            http_method='POST',
            queue_name='routes',
            schedule_time=60,
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
def test_edit_someone_else_route(seller, buyer, client_seller, faker, send_task):
    waypoints = [faker.address(), faker.address()]
    frequency = [1, 7]

    route_1 = baker.make(Route, user=buyer)

    response = client_seller.put(
        f'/routes/{route_1.id}', {'frequency': frequency, 'waypoints': waypoints}
    )

    assert response.status_code == 404

    response = client_seller.patch(f'/routes/{route_1.id}', {'waypoints': waypoints})

    assert response.status_code == 404

    assert not (
        mock.call(
            f"/detours/update/{route_1.id}",
            http_method='POST',
            queue_name='routes',
            schedule_time=60,
        )
        in send_task.call_args_list
    )
