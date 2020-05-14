from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from settings.models import Setting


@admin.register(Setting)
class SettingAdmin(BaseRegionalAdminMixin, VersionAdmin):
    ordering = ("id",)
    list_display = (
        "id",
        "charge",
        "mc_swiss_delivery_fee_vat",
        "platform_fee_vat",
        "transport_insurance",
        "deposit_vat",
        "min_purchase_value",
        "platform_user",
        "central_logistics_company",
        "logistics_company",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
