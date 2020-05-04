from django.conf import settings
from django.core import validators
from django.db import models

from common.models import Region
from core.db.base import BaseAbstractModel


class Setting(BaseAbstractModel):
    charge = models.DecimalField(max_digits=10, decimal_places=2)
    mc_swiss_delivery_fee_vat = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee_vat = models.DecimalField(max_digits=10, decimal_places=2)
    transport_insurance = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_vat = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_value = models.DecimalField(max_digits=10, decimal_places=2)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="settings", blank=False
    )
    platform_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="region_setting",
    )
    central_logistics_company = models.BooleanField(default=True)
    logistics_company = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    enable_platform_fee_share = models.BooleanField(
        default=False,
        help_text=(
            "Indicate if platform fee should be split between Traidoo "
            "Central and regional platform user"
        ),
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
            validators.MinValueValidator(0, message="Share should not be negative")
        ],
    )


def get_setting(region_id: int) -> Setting:
    return Setting.objects.filter(region_id=region_id).first()
