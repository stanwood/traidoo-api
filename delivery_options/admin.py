from django.contrib import admin
from django.contrib.admin import ModelAdmin

from delivery_options.models import DeliveryOption


@admin.register(DeliveryOption)
class DeliveryOptionAdmin(ModelAdmin):
    ordering = ("id",)
    list_display = (
        "id",
        "name",
    )
