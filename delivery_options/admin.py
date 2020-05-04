from django.contrib import admin
from reversion.admin import VersionAdmin

from delivery_options.models import DeliveryOption


@admin.register(DeliveryOption)
class DeliveryOptionAdmin(VersionAdmin):
    ordering = ('id', )
    list_display = (
        'id',
        'name',
    )
