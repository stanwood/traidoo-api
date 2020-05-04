from django.conf import settings
from django.db import models

from core.db.base import BaseAbstractModel


class DeliveryAddress(BaseAbstractModel):
    company_name = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ["id"]

    def as_str(self):
        return f"{self.company_name}, {self.street}, {self.zip}, {self.city}"
