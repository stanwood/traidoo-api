from enum import Enum

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from loguru import logger

from core.db.base import BaseAbstractModel
from routes.utils.route_length import calculate_route_length


class Days(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class Route(BaseAbstractModel):
    frequency = ArrayField(
        models.PositiveIntegerField(choices=[(day.value, day) for day in Days]), size=7
    )
    length = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="routes", on_delete=models.CASCADE
    )
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    waypoints = ArrayField(models.CharField(max_length=255), default=list, blank=True)

    def calculate_route_length(self):
        self.length = calculate_route_length(
            self.origin, self.destination, self.waypoints
        )
        logger.debug(f"Route ({self.id}) length: {self.length}")
