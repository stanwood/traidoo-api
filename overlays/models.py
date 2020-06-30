import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import Region
from core.db.base import BaseAbstractModel


def overlay_image_upload_to(instance, filename):
    _, filename_ext = os.path.splitext(filename)
    return f"public/{instance._meta.model_name}/{uuid.uuid4().hex}{filename_ext}"


class Overlay(BaseAbstractModel):
    OVERLAY_TYPE_ANONYMOUS = "anonymous"
    OVERLAY_TYPE_NOT_VERIFIED = "not_verified"
    OVERLAY_TYPE_NOT_COOPERATIVE = "not_cooperative"
    OVERLAY_TYPE_NOT_APPROVED = "not_approved"

    OVERLAY_TYPES = [
        (OVERLAY_TYPE_ANONYMOUS, _("Anonymous user")),
        (OVERLAY_TYPE_NOT_VERIFIED, _("Not verified user")),
        (OVERLAY_TYPE_NOT_COOPERATIVE, _("Not cooperative user")),
        (OVERLAY_TYPE_NOT_APPROVED, _("Not approved user")),
    ]

    overlay_type = models.CharField(
        max_length=20, choices=OVERLAY_TYPES, verbose_name=_("Overlay type")
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    subtitle = models.CharField(max_length=255, verbose_name=_("Subtitle"))
    body = models.TextField(verbose_name=_("Body"))
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="overlays",
        blank=False,
        null=False,
        help_text=_("Region"),
        verbose_name=_("Region"),
    )
    avatar = models.ImageField(
        upload_to=overlay_image_upload_to, verbose_name=_("Avatar"),
    )
    image = models.ImageField(
        upload_to=overlay_image_upload_to, verbose_name=_("Image"),
    )

    class Meta:
        verbose_name = _("Overlay")
        verbose_name_plural = _("Overlays")
        unique_together = ("overlay_type", "region")


class OverlayButton(BaseAbstractModel):
    overlay = models.ForeignKey(
        Overlay,
        related_name="buttons",
        on_delete=models.CASCADE,
        verbose_name=_("Overlay"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    url = models.CharField(max_length=255, verbose_name=_("URL"))
    order = models.PositiveIntegerField(verbose_name=_("Order"))

    class Meta:
        unique_together = ["overlay", "order"]
        verbose_name = _("Overlay button")
        verbose_name_plural = _("Overlay buttons")
