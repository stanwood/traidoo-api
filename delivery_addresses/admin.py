from django.contrib import admin
from reversion.admin import VersionAdmin

from delivery_addresses.models import DeliveryAddress


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(VersionAdmin):
    ordering = ('company_name', )
    list_display = (
        'id',
        'company_name',
        'street',
        'zip',
        'city',
        'user',
    )
    list_display_links = [
        'user',
    ]
