import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.db.base import BaseAbstractModel


def overlay_image_upload_to(instance, filename):
    _, filename_ext = os.path.splitext(filename)
    return f"public/{instance._meta.model_name}/{uuid.uuid4().hex}{filename_ext}"


class Overlay(BaseAbstractModel):
    OVERLAY_TYPE_ANONYMOUS = "anonymous"
    OVERLAY_TYPE_NOT_VERIFIED = "not_verified"
    OVERLAY_TYPE_NOT_COOPERATIVE = "not_cooperative"

    OVERLAY_TYPES = [
        (OVERLAY_TYPE_ANONYMOUS, _("Anonymous user")),
        (OVERLAY_TYPE_NOT_VERIFIED, _("Not verified user")),
        (OVERLAY_TYPE_NOT_COOPERATIVE, _("Not cooperative user")),
    ]

    overlay_type = models.CharField(
        max_length=20,
        choices=OVERLAY_TYPES,
        verbose_name=_("Overlay type"),
        unique=True,
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    subtitle = models.CharField(max_length=255, verbose_name=_("Subtitle"))
    body = models.TextField(verbose_name=_("Body"))
    learn_more_url = models.CharField(
        max_length=255, blank=True, verbose_name=_("Learn more URL")
    )
    avatar = models.ImageField(
        upload_to=overlay_image_upload_to, verbose_name=_("Avatar"),
    )
    image = models.ImageField(
        upload_to=overlay_image_upload_to, verbose_name=_("Image"),
    )
