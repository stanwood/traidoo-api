from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Job, Detour


@admin.register(Job)
class JobAdmin(ModelAdmin):
    ordering = ("created_at",)
    list_display = ("id", "user")
    list_display_links = ["user"]


@admin.register(Detour)
class DetourAdmin(ModelAdmin):
    ordering = ("id",)
    list_display = ("id", "length", "job", "route")
    list_display_links = ["job", "route"]
