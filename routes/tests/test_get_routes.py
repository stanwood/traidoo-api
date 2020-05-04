from unittest import mock

import pytest
from model_mommy import mommy

from ..models import Route


@pytest.mark.django_db
def test_get_only_own_routes(seller, buyer, client_seller, send_task):
    route_1 = mommy.make(Route, user=seller)
    mommy.make(Route, user=buyer)

    response = client_seller.get('/routes')

    assert response.json()['count'] == 1
    assert response.json()['next'] == None
    assert response.json()['previous'] == None
    assert response.json()['results'][0]['id'] == route_1.id
    assert response.json()['results'][0]['frequency'] == route_1.frequency
    assert response.json()['results'][0]['waypoints'] == route_1.waypoints
    assert response.json()['results'][0]['origin'] == route_1.origin
    assert response.json()['results'][0]['destination'] == route_1.destination
    assert response.json()['results'][0]['length'] == 0
    assert response.json()['results'][0]['createdAt']
    assert response.json()['results'][0]['updatedAt']

    assert not (
        mock.call(
            f'/routes/{route_1.id}/calculate_route_length',
            http_method='POST',
            queue_name='routes',
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
def test_get_single_route(seller, client_seller, send_task):
    route = mommy.make(Route, user=seller)

    response = client_seller.get(f'/routes/{route.id}')

    assert response.json()['id'] == route.id
    assert response.json()['frequency'] == route.frequency
    assert response.json()['waypoints'] == route.waypoints
    assert response.json()['origin'] == route.origin
    assert response.json()['destination'] == route.destination
    assert response.json()['length'] == 0
    assert response.json()['createdAt']
    assert response.json()['updatedAt']

    assert not (
        mock.call(
            f'/routes/{route.id}/calculate_route_length',
            http_method='POST',
            queue_name='routes',
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
def test_get_someone_else_route(buyer, client_seller, send_task):
    route = mommy.make(Route, user=buyer)

    response = client_seller.get(f'/routes/{route.id}')

    assert response.status_code == 404

    assert not (
        mock.call(
            f'/routes/{route.id}/calculate_route_length',
            http_method='POST',
            queue_name='routes',
        )
        in send_task.call_args_list
    )
