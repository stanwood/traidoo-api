import base64
import json
from itertools import groupby

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.client.exceptions import MangopayError
from payments.mixins import MangopayMixin
from users.models import KycDocument

from ..serializers.documents import UserMangopayDocumentsSerializer


class MangopayDocumentsView(generics.ListCreateAPIView, MangopayMixin):
    queryset = KycDocument.objects.all()
    parser_classes = (MultiPartParser,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        try:
            response = self.mangopay.get_user_kyc_documents(
                request.user.mangopay_user_id
            )
        except MangopayError as err:
            return Response(
                {"message": json.loads(err.args[0].decode())["Message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sorted_response = sorted(response, key=lambda k: k["Type"], reverse=True)
        grouped_by_type = groupby(sorted_response, lambda a: a["Type"])

        return Response(
            [
                sorted(list(items), key=lambda k: k["CreationDate"], reverse=True)[0]
                for _, items in grouped_by_type
            ]
        )

    def create(self, request, *args, **kwargs):
        serializer = UserMangopayDocumentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_mangopay_id = request.user.mangopay_user_id
        file_content = serializer.validated_data["file"].read()

        try:
            self.upload_kyc_document(
                user_mangopay_id,
                serializer.validated_data["document_type"],
                base64.b64encode(file_content).decode(),
            )
        except MangopayError as err:
            return Response(
                {"error": json.loads(err.args[0].decode())["Message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
