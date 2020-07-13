from django.contrib import admin
from django.contrib.admin import ModelAdmin

from common.admin import BaseRegionalAdminMixin
from core.mixins.storage import StorageMixin
from documents.models import Document
from orders.models import Order, OrderItem


class OrderItemsInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = [
        "product",
        "quantity",
        "latest_delivery_date",
        "delivery_option",
        "delivery_date",
        "delivery_company",
        "delivery_fee",
        "price",
    ]

    readonly_fields = ["delivery_date", "delivery_company", "delivery_fee", "price"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_admin or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class DocumentsInline(StorageMixin, admin.TabularInline):
    model = Document
    extra = 0

    fields = [
        "document_type",
        "seller_company_name",
        "buyer_company_name",
        "payment_reference",
        "mangopay_payin_id",
        "price",
        "paid",
        "is_invoice",
        "pdf_file",
    ]
    readonly_fields = [
        "seller_company_name",
        "buyer_company_name",
        "price",
        "is_invoice",
        "pdf_file",
    ]

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_admin or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def pdf_file(self, obj):
        return self.bucket.blob(obj.blob_name).generate_signed_url(expiration=60)


@admin.register(Order)
class OrderAdmin(BaseRegionalAdminMixin, ModelAdmin):
    ordering = ("-earliest_delivery_date",)
    inlines = (OrderItemsInline, DocumentsInline)
    list_display = (
        "id",
        "buyer",
        "status",
        "total_price",
        "earliest_delivery_date",
        "created_at",
    )
    list_display_links = ["buyer"]
    list_filter = ["status"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_admin or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    ordering = ("-latest_delivery_date",)
    list_display = (
        "id",
        "product",
        "order",
        "latest_delivery_date",
        "delivery_address",
        "quantity",
        "delivery_option",
    )
    list_display_links = ["product", "order", "delivery_address", "delivery_option"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_admin or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
