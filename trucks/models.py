from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.db.base import BaseAbstractModel


class Truck(BaseAbstractModel):
    class Meta:
        verbose_name = _("Truck")
        verbose_name_plural = _("Trucks")

    name = models.CharField(unique=True, max_length=255, verbose_name=_("Truck"))
