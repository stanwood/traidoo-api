from django.db import models
from django.utils.translation import gettext_lazy as _

from core.db.base import BaseAbstractModel

from products.models import Product


class Item(BaseAbstractModel):
    product = models.ForeignKey(
        Product,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_("Product"),
    )
    latest_delivery_date = models.DateField(verbose_name=_("Latest delivery date"))
    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))
    valid_from = models.DateField(
        null=True, blank=True, verbose_name=_("Date valid from")
    )

    class Meta:
        unique_together = (("product", "latest_delivery_date"),)
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
