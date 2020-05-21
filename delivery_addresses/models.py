from django.conf import settings
from django.db import models

from core.db.base import BaseAbstractModel
from django.utils.translation import gettext_lazy as _


class DeliveryAddress(BaseAbstractModel):
    company_name = models.CharField(max_length=255, verbose_name=_("Company name"))
    street = models.CharField(max_length=255, verbose_name=_("Street"))
    zip = models.CharField(max_length=255, verbose_name=_("Zip code"))
    city = models.CharField(max_length=255, verbose_name=_("City"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User")
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Delivery address")
        verbose_name_plural = _("Delivery addresses")

    def as_str(self):
        return f"{self.company_name}, {self.street}, {self.zip}, {self.city}"
