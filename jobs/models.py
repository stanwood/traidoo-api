from django.conf import settings
from django.db import models

from core.db.base import BaseAbstractModel
from orders.models import OrderItem
from routes.models import Route


class Job(BaseAbstractModel):
    order_item = models.OneToOneField(
        OrderItem, related_name="job", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )


class Detour(BaseAbstractModel):
    job = models.ForeignKey(Job, related_name="detours", on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    length = models.PositiveIntegerField(default=0)
