from django.db import models

from core.db.base import BaseAbstractModel


class Truck(BaseAbstractModel):
    name = models.CharField(unique=True, max_length=255)
