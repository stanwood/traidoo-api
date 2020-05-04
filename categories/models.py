from django.db import models

from core.db.base import BaseAbstractModel


class Category(BaseAbstractModel):
    icon = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    ordering = models.IntegerField(null=True, blank=True)
    default_vat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subcategories', null=True, blank=True)
