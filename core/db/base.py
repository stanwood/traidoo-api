from django.db import models


class BaseAbstractModel(models.Model):
    id = models.BigAutoField(primary_key=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False
    )

    class Meta:
        abstract = True
