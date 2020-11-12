import os

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions.admin import IsAdminUser
from documents.models import Document

User = get_user_model()


class DownloadDocument(APIView):
    def _check_permissions(self, document: Document, user: User):
        return (
            document.seller["user_id"] == user.id
            or document.buyer["user_id"] == user.id
            or user.is_admin
            or user.is_superuser
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


class DownloadDocumentAdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, document_id: int):
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            raise Http404("Document not found")

        if not request.user.is_superuser and request.user.region not in (
            document.seller.get("region_id"),
            document.buyer.get("region_id"),
        ):
            raise PermissionDenied("You are not admin of the document region")

        return HttpResponseRedirect(document.signed_download_url)
