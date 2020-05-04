from django.db import models

from core.db.base import BaseAbstractModel

from products.models import Product


class Item(BaseAbstractModel):
    product = models.ForeignKey(
        Product, related_name='items', on_delete=models.CASCADE
    )
    latest_delivery_date = models.DateField()
    quantity = models.IntegerField()
    valid_from = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (('product', 'latest_delivery_date'), )
