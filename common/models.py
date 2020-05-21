from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField

from core.db.base import BaseAbstractModel
from core.storage.utils import public_logo_upload_to
from django.utils.translation import gettext_lazy as _


class Region(BaseAbstractModel):
    name = models.CharField(
        max_length=32, blank=False, unique=True, verbose_name=_("Name")
    )
    slug = models.SlugField(unique=True, blank=False, verbose_name=_("Slug"))
    website_slogan = models.CharField(
        max_length=255, blank=True, verbose_name=_("Slogan used in emails")
    )
    mail_footer = HTMLField(blank=True, verbose_name=_("Mail footer"))
    mail_logo = models.ImageField(
        blank=True,
        null=True,
        upload_to=public_logo_upload_to,
        verbose_name=_("Mail logo"),
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def setting(self):
        return self.settings.first()

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
