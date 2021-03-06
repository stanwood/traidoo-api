"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

"""

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from admin_tools.menu import Menu, items
from django.utils.translation import ugettext_lazy as _


class CustomMenu(Menu):
    def __init__(self, **kwargs):
        Menu.__init__(self, **kwargs)
        self.children += [
            items.MenuItem(_("Dashboard"), reverse("admin:index")),
            items.MenuItem(_("Users"), reverse("admin:users_user_changelist")),
            items.MenuItem(
                _("Containers"), reverse("admin:containers_container_changelist")
            ),
            items.MenuItem(
                _("Categories"), reverse("admin:categories_category_changelist")
            ),
            items.MenuItem(_("Products"), reverse("admin:products_product_changelist")),
            items.MenuItem(_("Orders"), reverse("admin:orders_order_changelist")),
            items.MenuItem(
                _("Logistics"),
                children=[
                    items.MenuItem(
                        _("Routes"), reverse("admin:routes_route_changelist")
                    ),
                    items.MenuItem(_("Jobs"), reverse("admin:jobs_job_changelist")),
                    items.MenuItem(
                        _("Trucks"), reverse("admin:trucks_truck_changelist")
                    ),
                ],
            ),
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """

        settings_menu = [
            items.MenuItem(
                _("Overlays"), reverse("admin:overlays_overlay_changelist")
            ),
            items.MenuItem(
                _("Region"), reverse("admin:common_region_changelist")
            ),
            items.MenuItem(
                _("Settings"), reverse("admin:settings_setting_changelist")
            ),
        ]

        if context.request.user.is_superuser:
            settings_menu += [
                items.MenuItem(
                    _("Global settings"),
                    reverse("admin:settings_globalsetting_changelist"),
                ),
            ]

        self.children += [
            items.MenuItem(
                _("Settings"),
                children=settings_menu,
            ),
        ]

        return super(CustomMenu, self).init_with_context(context)
