from django.core import validators
from django.utils.translation import gettext_lazy as _
from django.db import models

from core.db.base import BaseAbstractModel
from core.storage.utils import public_image_upload_to


class Container(BaseAbstractModel):
    size_class = models.CharField(
        unique=True, max_length=255, verbose_name=_("Size class")
    )
    standard = models.BooleanField(
        null=True, blank=True, verbose_name=_("Standard container")
    )
    volume = models.FloatField(
        validators=[
            validators.MinValueValidator(
                0, message=_("Container volume cannot be negative")
            )
        ],
        verbose_name=_("Volume"),
    )
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            validators.MinValueValidator(
                0, message=_("Container deposit cannot be negative")
            )
        ],
        verbose_name=_("Depoisit"),
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            validators.MinValueValidator(
                0, message=_("Container delivery fee cannot be negative")
            )
        ],
        verbose_name=_("Delivery fee"),
    )
    image_url = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Image url")
    )
    image = models.ImageField(
        upload_to=public_image_upload_to, null=True, blank=True, verbose_name=_("Image")
    )

    def __str__(self):
        return f"{self.size_class} {self.volume}"

    class Meta:
        verbose_name = _("Container")
        verbose_name_plural = _("Containers")
