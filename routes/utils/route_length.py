from typing import List

import googlemaps
from django.conf import settings
from googlemaps.exceptions import ApiError
from loguru import logger


def calculate_route_length(origin: str, destination: str, waypoints: List[str]) -> int:
    gmaps = googlemaps.Client(key=settings.GOOGLE_KEYS['DISTANCE_MATRIX_API_KEY'])

    try:
        response = gmaps.directions(
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            mode='driving',
            units='metric',
            optimize_waypoints=True,
        )
    except ApiError as err:
        logger.debug(f'GoogleDistanceAPI: Route not found: {err}')
        return 0

    try:
        response[0]['legs']
    except (IndexError, KeyError):
        logger.debug('GoogleDistanceAPI: Response has no legs')
        return 0

    return sum(leg['distance']['value'] for leg in response[0]['legs'])
