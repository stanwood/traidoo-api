from django.contrib import admin
from django.contrib.admin import ModelAdmin

from documents.models import Document


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "id",
        "document_type",
        "order",
        "payment_reference",
        "mangopay_payin_id",
        "bank_account_owner",
        "paid",
        "created_at",
    )
    list_display_links = ["order"]
    list_filter = ["paid"]
