import datetime

from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.db.base import BaseAbstractModel

from products.models import Product


class Item(BaseAbstractModel):
    product = models.ForeignKey(Product, related_name="items", on_delete=models.CASCADE)
    latest_delivery_date = models.DateField()
    quantity = models.PositiveIntegerField()
    valid_from = models.DateField(null=True, blank=True,)

    class Meta:
        unique_together = (("product", "latest_delivery_date"),)
        verbose_name = _("Items")
