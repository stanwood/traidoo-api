from django.contrib.auth import get_user_model

from documents.models import Document

User = get_user_model()


def get_buyer_document_types(user: User):
    document_types = [
        Document.TYPES.logistics_invoice.value[0],
        Document.TYPES.producer_invoice.value[0],
        Document.TYPES.delivery_overview_buyer.value[0],
        Document.TYPES.order_confirmation_buyer.value[0],
    ]

    if user.is_cooperative_member:
        document_types.append(Document.TYPES.buyer_platform_invoice.value[0])

    return document_types


def get_seller_document_types():
    return [
        Document.TYPES.producer_invoice.value[0],
        Document.TYPES.platform_invoice.value[0],
        Document.TYPES.delivery_overview_seller.value[0],
    ]
