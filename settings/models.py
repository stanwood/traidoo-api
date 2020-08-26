from django.conf import settings
from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField

from common.models import Region
from core.db.base import BaseAbstractModel


class GlobalSetting(BaseAbstractModel):
    product_vat = ArrayField(
        models.DecimalField(
            max_digits=10,
            decimal_places=2,
            validators=[
                validators.MaxValueValidator(
                    100, _("VAT should not be more than 100%")
                ),
                validators.MinValueValidator(0, _("VAT should not be negative")),
            ],
        ),
        verbose_name=_("Available product VAT rates"),
    )

    class Meta:
        verbose_name = _("Global setting")
        verbose_name_plural = _("Global settings")


class Setting(BaseAbstractModel):
    class Meta:
        verbose_name = _("Setting")
        verbose_name_plural = _("Settings")

    charge = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Platform charge rate")
    )
    mc_swiss_delivery_fee_vat = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Central delivery fee VAT rate")
    )
    platform_fee_vat = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Platform fee VAT rate")
    )
    transport_insurance = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Transport insurance rate")
    )
    deposit_vat = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Deposit VAT rate")
    )
    min_purchase_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Min purchase value")
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="settings",
        blank=False,
        verbose_name=_("Region"),
    )
    platform_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="region_setting",
        verbose_name=_("Platform user account"),
    )
    central_logistics_company = models.BooleanField(
        default=True, verbose_name=_("Central logistic company available")
    )
    logistics_company = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Logistics company account"),
    )
    enable_platform_fee_share = models.BooleanField(
        default=False,
        help_text=(
            "Indicate if platform fee should be split between Traidoo "
            "Central and regional platform user"
        ),
        verbose_name=_("Enable platform fee share"),
    )
    central_share = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=(
            "Describes (in %) how much of platform fee should go to Traidoo "
            "Central. The rest will be transferred to regional platform user."
        ),
        validators=[
            validators.MaxValueValidator(100),
            validators.MinValueValidator(0, message="Share should not be negative"),
        ],
        verbose_name=_("Central platform share"),
    )


def get_setting(region_id: int) -> Setting:
    return Setting.objects.filter(region_id=region_id).first()
