import json

from django.conf import settings
from django.core import validators
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

BASE_UNITS = (
    ("weight", _("Weight (g) per item")),
    ("volume", _("Volume (l) per item")),
)


class BigAutoFieldTaggedItem(CommonGenericTaggedItemBase, TaggedItemBase):
    object_id = models.BigIntegerField(verbose_name=_("Object id"), db_index=True)


class Product(BaseAbstractModel):
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    image_url = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Image url")
    )
    image = models.ImageField(
        upload_to=public_image_upload_to, null=True, blank=True, verbose_name=_("Image")
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="products",
        blank=False,
        help_text=_("Region of origin"),
        verbose_name=_("Region of origin"),
    )
    regions = models.ManyToManyField(
        Region,
        help_text=_("The associated regions the product should be available in"),
        verbose_name=_("Available in regions"),
    )

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, verbose_name=_("Category")
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Seller")
    )

    is_organic = models.BooleanField(default=False, verbose_name=_("Is organic"))
    is_vegan = models.BooleanField(default=False, verbose_name=_("Is vegan"))
    is_gluten_free = models.BooleanField(
        default=False, verbose_name=_("Is gluten free")
    )
    is_grazing_animal = models.BooleanField(
        default=False, verbose_name=_("Is grazing animal")
    )
    is_gmo_free = models.BooleanField(default=False, verbose_name=_("Is GMO free"))

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount in a lot"),
        validators=[
            validators.MinValueValidator(0, message=_("Amount should not be negative"))
        ],
    )
    unit = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Unit")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price"),
        validators=[
            validators.MinValueValidator(0, message=_("Price should not be negative"))
        ],
    )
    vat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("VAT rate"),
        validators=[
            validators.MaxValueValidator(100, _("VAT should not be more than 100%")),
            validators.MinValueValidator(0, message=_("VAT should not be negative")),
        ],
    )

    container_type = models.ForeignKey(
        Container, on_delete=models.PROTECT, verbose_name=_("Container type")
    )
    container_description = models.TextField(
        null=True, blank=True, verbose_name=_("Container description")
    )

    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[
            validators.MinValueValidator(
                0, message=_("Delivery charge should not be negative")
            )
        ],
        verbose_name=_("Delivery charge"),
    )
    delivery_options = models.ManyToManyField(
        DeliveryOption, verbose_name=_("Delivery options")
    )
    third_party_delivery = models.BooleanField(
        default=False, verbose_name=_("Third party delivery possible")
    )
    delivery_requirements = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Delivery requirements")
    )

    tags = TaggableManager(through=BigAutoFieldTaggedItem, verbose_name=_("Tags"))

    ean8 = models.CharField(max_length=255, null=True, blank=True)
    ean13 = models.CharField(max_length=255, null=True, blank=True)

    sellers_product_identifier = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Sellers product identifier"),
    )

    base_unit = models.CharField(
        max_length=16, choices=BASE_UNITS, blank=True, verbose_name=_("Base unit")
    )
    item_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            validators.MinValueValidator(
                0, message=_("Items quantity should not be negative")
            )
        ],
        verbose_name=_("Item quantity"),
    )

    def create_snapshot(self):
        from products.serializers import ProductSnapshotSerializer

        return json.loads(JSONRenderer().render(ProductSnapshotSerializer(self).data))

    def first_available_delivery_option(self):
        if self.region.settings.first().central_logistics_company:
            return self.delivery_options.first()

        return self.delivery_options.exclude(
            id=DeliveryOption.CENTRAL_LOGISTICS
        ).first()

    def __str__(self):
        return self.name
