from django.contrib import admin
from django.contrib.admin import ModelAdmin

from trucks.models import Truck


@admin.register(Truck)
class TruckAdmin(ModelAdmin):
    ordering = ("name",)
    list_display = (
        "id",
        "name",
    )
