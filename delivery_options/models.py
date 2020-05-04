from django.db import models


class DeliveryOption(models.Model):
    CENTRAL_LOGISTICS = 0
    SELLER = 1
    BUYER = 2

    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
