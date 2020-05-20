from enum import Enum

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.db.base import BaseAbstractModel
from core.storage.private_storage import private_storage
from core.storage.utils import private_image_upload_to


class KycDocument(BaseAbstractModel):
    class Name(Enum):
        IDENTITY_PROOF = "IDENTITY_PROOF"
        ARTICLES_OF_ASSOCIATION = "ARTICLES_OF_ASSOCIATION"
        REGISTRATION_PROOF = "REGISTRATION_PROOF"
        ADDRESS_PROOF = "ADDRESS_PROOF"
        SHAREHOLDER_DECLARATION = "SHAREHOLDER_DECLARATION"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User")
    )
    name = models.CharField(
        choices=[(name, name.value) for name in Name],
        max_length=30,
        verbose_name=_("Name"),
    )
    file = models.FileField(
        upload_to=private_image_upload_to,
        storage=private_storage,
        null=True,
        blank=True,
        verbose_name=_("File"),
    )

    class Meta:
        unique_together = ["user", "name"]
        verbose_name = _("KYC document")
        verbose_name_plural = _("KYC documents")
