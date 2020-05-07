from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField

from core.db.base import BaseAbstractModel
from core.storage.utils import public_logo_upload_to


class Region(BaseAbstractModel):
    name = models.CharField(max_length=32, blank=False, unique=True)
    slug = models.SlugField(unique=True, blank=False)
    website_slogan = models.CharField(
        max_length=255, blank=True, verbose_name="Slogan used in emails"
    )
    mail_footer = HTMLField(blank=True)
    mail_logo = models.ImageField(
        blank=True, null=True, upload_to=public_logo_upload_to
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def setting(self):
        return self.settings.first()

    @property
    def region_id(self):
        return self.id

    @region_id.setter
    def region_id(self, region_id):
        """ Dummy to keep admin code simpler and allow setting region id when editing region"""
        pass
