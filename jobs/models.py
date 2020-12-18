from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.db.base import BaseAbstractModel

from routes.models import Route


class Job(BaseAbstractModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("User"),
    )

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")


class Detour(BaseAbstractModel):
    job = models.ForeignKey(
        Job, related_name="detours", on_delete=models.CASCADE, verbose_name=_("Job")
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE, verbose_name=_("Route"))
    length = models.PositiveIntegerField(default=0, verbose_name=_("Lenght"))

    class Meta:
        verbose_name = _("Detour")
        verbose_name_plural = _("Detours")
