from enum import Enum

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField

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
    class Meta:
        verbose_name = _("Route")
        verbose_name_plural = _("Routes")

    frequency = ArrayField(
        models.PositiveIntegerField(choices=[(day.value, day) for day in Days]),
        size=7,
        verbose_name=_("Frequency"),
        help_text=_("1 - Monday, 2 - Tuesday etc.")
    )
    length = models.PositiveIntegerField(default=0, verbose_name=_("Length"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="routes",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    origin = models.CharField(max_length=255, verbose_name=_("Origin"))
    destination = models.CharField(max_length=255, verbose_name=_("Destination"))
    waypoints = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True,
        verbose_name=_("Way points"),
    )

    def calculate_route_length(self):
        self.length = calculate_route_length(
            self.origin, self.destination, self.waypoints
        )
        logger.debug(f"Route ({self.id}) length: {self.length}")
