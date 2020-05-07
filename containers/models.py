from django.utils.translation import gettext_lazy as _
from django.db import models

from core.db.base import BaseAbstractModel
from core.storage.utils import public_image_upload_to


class Container(BaseAbstractModel):
    size_class = models.CharField(unique=True, max_length=255)
    standard = models.BooleanField(null=True, blank=True)
    volume = models.FloatField()
    deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to=public_image_upload_to, null=True, blank=True)

    def __str__(self):
        return f"{self.size_class} {self.volume}"

    class Meta:
        verbose_name = _("Container")
        verbose_name_plural = _("Containers")
