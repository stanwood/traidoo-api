from django.db import models
from django.utils.translation import gettext_lazy as _

from core.db.base import BaseAbstractModel


class Category(BaseAbstractModel):
    icon = models.CharField(max_length=255)
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    ordering = models.IntegerField(null=True, blank=True)
    default_vat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Default VAT Rate"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        null=True,
        blank=True,
        verbose_name=_("Parent category"),
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
