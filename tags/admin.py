from django.contrib import admin
from reversion.admin import VersionAdmin

from taggit.models import Tag


@admin.register(Tag)
class TagAdmin(VersionAdmin):
    ordering = ('name', )
    list_display = (
        'id',
        'name',
        'slug',
    )
