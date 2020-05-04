import base64
import json

from loguru import logger
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions.task import IsTask
from payments.client.exceptions import MangopayError
from payments.mixins import MangopayMixin
from users.models import KycDocument


class UploadUserMangopayKycDocumentView(MangopayMixin, views.APIView):
    permission_classes = (AllowAny, IsTask)

    def post(self, request, document_id, format=None):
        try:
            document = KycDocument.objects.get(id=document_id)
        except KycDocument.DoesNotExist:
            logger.error(f"KYC document with ID {document_id} does not exist.")
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            self.upload_kyc_document(
                document.user.mangopay_user_id,
                document.name,
                base64.b64encode(document.file.read()).decode(),
            )
        except MangopayError as err:
            return Response(
                {"error": json.loads(err.args[0].decode())["Message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            document.file.delete()
            document.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
