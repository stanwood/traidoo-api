import datetime
import os

import google.cloud.storage
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from documents.utils.document_types import (
    get_buyer_document_types,
    get_seller_document_types,
)

User = get_user_model()


class DownloadDocument(APIView):
    def _check_permissions(self, document: Document, user: User):
        if user.is_buyer:
            return (
                document.order.buyer == user
                and document.document_type in get_buyer_document_types(user)
            )
        elif user.is_seller:
            return (
                document.seller["user_id"] == user.id
                and document.document_type in get_seller_document_types()
            )
        else:
            return False

    def get(self, request: Request, document_id: int = None, format: str = None):
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not self._check_permissions(document, request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        storage_client = google.cloud.storage.Client.from_service_account_json(
            settings.BASE_DIR.joinpath("service_account.json")
        )

        bucket = storage_client.get_bucket(settings.DEFAULT_BUCKET)
        blob = bucket.blob(document.blob_name)

        filename = os.path.basename(document.blob_name)

        return Response(
            {
                "url": blob.generate_signed_url(
                    datetime.timedelta(minutes=settings.DOCUMENTS_EXPIRATION_TIME),
                    response_disposition=f"attachment; filename={filename}",
                ),
                "filename": filename,
            }
        )
