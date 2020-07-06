from django.contrib import admin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from reversion.admin import VersionAdmin

from .models import Route


@admin.register(Route)
class RouteAdmin(VersionAdmin, DynamicArrayMixin):
    ordering = ("id",)
    list_display = (
        "id",
        "user",
        "length",
        "origin",
        "waypoints",
        "destination",
        "frequency",
    )

    def save_model(self, request, obj, form, change):
        route_properties = {"waypoints", "origin", "destination"}
        changed_data = set(form.changed_data)
        # bugfix - empty list of waypoints not saved with `form.save_form()`
        if not form.cleaned_data["waypoints"]:
            obj.waypoints = []
        route_length_changed = bool(changed_data.intersection(route_properties))
        if route_length_changed:
            obj.calculate_route_length()
        return super(RouteAdmin, self).save_model(request, obj, form, change)
