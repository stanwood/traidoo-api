import json

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework.renderers import JSONRenderer
from taggit.managers import TaggableManager
from taggit.models import CommonGenericTaggedItemBase, TaggedItemBase

from categories.models import Category
from common.models import Region
from containers.models import Container
from core.db.base import BaseAbstractModel
from core.storage.utils import public_image_upload_to
from delivery_options.models import DeliveryOption

BASE_UNITS = (("weight", "Weight (g) per item"), ("volume", "Volume (l) per item"))


class BigAutoFieldTaggedItem(CommonGenericTaggedItemBase, TaggedItemBase):
    object_id = models.BigIntegerField(verbose_name=_("Object id"), db_index=True)


class Product(BaseAbstractModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to=public_image_upload_to, null=True, blank=True)
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="products",
        blank=False,
        help_text="Region of origin",
    )
    regions = models.ManyToManyField(
        Region, help_text="The associated regions the product should be available in",
    )

    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    is_organic = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_grazing_animal = models.BooleanField(default=False)
    is_gmo_free = models.BooleanField(default=False)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.DecimalField(max_digits=10, decimal_places=2)

    container_type = models.ForeignKey(Container, on_delete=models.PROTECT)
    container_description = models.TextField(null=True, blank=True)

    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_options = models.ManyToManyField(DeliveryOption)
    third_party_delivery = models.BooleanField(default=False)
    delivery_requirements = models.CharField(max_length=255, null=True, blank=True)

    tags = TaggableManager(through=BigAutoFieldTaggedItem)

    ean8 = models.CharField(max_length=255, null=True, blank=True)
    ean13 = models.CharField(max_length=255, null=True, blank=True)

    sellers_product_identifier = models.CharField(max_length=255, null=True, blank=True)

    base_unit = models.CharField(max_length=16, choices=BASE_UNITS, blank=True)
    item_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def create_snapshot(self):
        from products.serializers import SimpleProductSerializer

        return json.loads(JSONRenderer().render(SimpleProductSerializer(self).data))

    def first_available_delivery_option(self):
        if self.region.settings.first().central_logistics_company:
            return self.delivery_options.first()

        return self.delivery_options.exclude(
            id=DeliveryOption.CENTRAL_LOGISTICS
        ).first()

    def __str__(self):
        return self.name
