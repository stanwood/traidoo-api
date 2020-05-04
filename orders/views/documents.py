import datetime
import os
from rest_framework import status, views
from rest_framework import viewsets
from rest_framework.response import Response
import google.cloud.storage

from rest_framework.permissions import IsAuthenticated
from core.permissions.buyer import IsBuyerOrAdminUser
from core.permissions.seller import IsSellerOrAdminUser
from documents.models import Document
from ..serializers import OrderDocumentSerializer
from rest_framework.decorators import action
from django.conf import settings


class OrderDocumentsView(viewsets.ModelViewSet):
    serializer_class = OrderDocumentSerializer
    permission_classes = (IsBuyerOrAdminUser | IsSellerOrAdminUser,)

    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        queryset = Document.objects.filter(order_id=self.kwargs['order_pk'])

        if self.request.user.is_seller:
            queryset = queryset.filter(seller__user_id=self.request.user.id)

        return queryset

    @action(detail=True)
    def download(self, request, order_pk=None, pk=None):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not self.request.user.approved:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if (
            self.request.user.is_seller
            and document.seller.get('user_id') != self.request.user.id
        ):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        storage_client = google.cloud.storage.Client.from_service_account_json(
            settings.BASE_DIR.joinpath('service_account.json')
        )
        bucket = storage_client.get_bucket(settings.DEFAULT_BUCKET)
        blob = bucket.blob(document.blob_name)

        filename = os.path.basename(document.blob_name)

        return Response(
            {
                'url': blob.generate_signed_url(
                    datetime.timedelta(minutes=settings.DOCUMENTS_EXPIRATION_TIME),
                    response_disposition=f'attachment; filename={filename}',
                ),
                'filename': filename,
            }
        )
