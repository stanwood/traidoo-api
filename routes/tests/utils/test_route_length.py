import json
from pathlib import Path
from unittest import mock

import pytest

from ...utils.route_length import calculate_route_length


@pytest.mark.django_db
@mock.patch('routes.utils.route_length.googlemaps')
def test_route_length(googlemaps_mock):
    route = [
        'Poznań, Brzask 21',
        'Poznań, Brzask 27',
        'Poznań, Morawskiego 25',
        'Poznań, Morawskiego 12',
    ]

    with open(
        Path(__file__).parent / 'data/google_directions_api_response.json'
    ) as json_file:
        google_directions_api_response = json.load(json_file)

    googlemaps_mock.Client.return_value.directions.return_value = (
        google_directions_api_response
    )

    length = calculate_route_length(route[0], route[-1], route[1:-1])

    assert length == 2678
    googlemaps_mock.Client.return_value.directions.assert_called_once_with(
        destination=route[-1],
        mode='driving',
        optimize_waypoints=True,
        origin=route[0],
        units='metric',
        waypoints=route[1:-1],
    )
