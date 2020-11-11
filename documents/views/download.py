import os

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document

User = get_user_model()


class DownloadDocument(APIView):
    def _check_permissions(self, document: Document, user: User):
        return (
            document.seller["user_id"] == user.id
            or document.buyer["user_id"] == user.id
        )

    def get(self, request: Request, document_id: int = None, format: str = None):
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not self._check_permissions(document, self.request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        filename = os.path.basename(document.blob_name)

        return Response(
            {
                "url": document.signed_download_url,
                "filename": filename,
            }
        )
