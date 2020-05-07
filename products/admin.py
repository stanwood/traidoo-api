from django.contrib import admin
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from items.models import Item
from products.models import Product


class ItemsInline(BaseRegionalAdminMixin, admin.TabularInline):
    model = Item
    extra = 1


@admin.register(Product)
class ProductAdmin(BaseRegionalAdminMixin, VersionAdmin):
    list_display = (
        "id",
        "name",
        "is_organic",
        "is_vegan",
        "is_gluten_free",
        "unit",
        "price",
        "region",
    )
    search_fields = ("name", "category__name")

    list_filter = ("region", "category")

    inlines = (ItemsInline,)

    exclude = ["region"]

    def get_field_queryset(self, db, db_field, request):
        queryset = super(ProductAdmin, self).get_field_queryset(db, db_field, request)
        if db_field.name == "seller":
            queryset = queryset.filter(region=request.user.region)
        elif db_field.name == "region":
            pass
        return queryset
