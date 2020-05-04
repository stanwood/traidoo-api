from django.contrib import admin
from reversion.admin import VersionAdmin

from containers.models import Container


@admin.register(Container)
class ContainerAdmin(VersionAdmin):
    ordering = ('size_class', )
    list_display = (
        'id',
        'size_class',
        'standard',
        'volume',
        'deposit',
        'delivery_fee',
        'image_url',
    )
