from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Job, Detour


@admin.register(Job)
class JobAdmin(VersionAdmin):
    ordering = ('created_at',)
    list_display = ('id', 'user', 'order_item')
    list_display_links = ['user', 'order_item']


@admin.register(Detour)
class DetourAdmin(VersionAdmin):
    ordering = ('id',)
    list_display = ('id', 'length', 'job', 'route')
    list_display_links = ['job', 'route']

