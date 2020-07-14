from django.contrib import admin
from django.contrib.admin import ModelAdmin

from taggit.models import Tag


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    ordering = ("name",)
    list_display = (
        "id",
        "name",
        "slug",
    )
