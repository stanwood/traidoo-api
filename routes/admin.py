from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Route


@admin.register(Route)
class RouteAdmin(VersionAdmin):
    ordering = ('id',)
    list_display = ('id', 'user', 'length', 'created_at', 'updated_at')
