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

User = get_user_model()


class DownloadDocument(APIView):
    def _check_permissions(self, document: Document, user: User):
        # TODO: implement permissions
        pass

    def get(self, request: Request, document_id: int = None, format: str = None):
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

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
