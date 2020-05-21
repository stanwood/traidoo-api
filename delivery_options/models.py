from django.utils.translation import gettext_lazy as _
from django.db import models


class DeliveryOption(models.Model):
    CENTRAL_LOGISTICS = 0
    SELLER = 1
    BUYER = 2

    name = models.CharField(max_length=255, verbose_name=_("Name"))

    created_at = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_("Created at")
    )
    updated_at = models.DateTimeField(
        auto_now=True, editable=False, verbose_name=_("Last update at")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Delivery option")
        verbose_name_plural = _("Delivery options")
