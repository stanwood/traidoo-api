from django.contrib import admin
from reversion.admin import VersionAdmin

from trucks.models import Truck


@admin.register(Truck)
class TruckAdmin(VersionAdmin):
    ordering = ('name', )
    list_display = (
        'id',
        'name',
    )
