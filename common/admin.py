from django.contrib import admin

from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class BaseRegionalAdminMixin:
    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_admin:
            queryset = queryset.filter(region_id=request.user.region.id)

        return queryset
