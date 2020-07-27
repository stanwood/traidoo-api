from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from trans import trans

from core.mixins.storage import StorageMixin
from core.permissions.cron_or_task import IsCronOrTask
from documents.models import Document
from mails.utils import send_mail
from orders.models import Order


class MailDocumentsTask(StorageMixin, views.APIView):
    permission_classes = (IsCronOrTask,)

    def post(self, request: Request, order_id: str, email: str):
        documents = Document.objects.filter(order_id=order_id)
        order = Order.objects.get(id=order_id)
        documents_to_send = [
            document for document in documents if email in document.receivers_emails
        ]

        attachments_as_blobs = [
            self.bucket.blob(document.blob_name) for document in documents_to_send
        ]

        send_mail(
            region=order.region,
            subject=f"Bestellbestätigung für #{order.id}",
            recipient_list=[email],
            template="mails/generic.html",
            context={
                "body": (
                    f"Ihre Unterlagen für die Bestellung #{order.id} finden "
                    f"Sie im Anhang dieser E-Mail"
                )
            },
            attachments=[
                (
                    trans(blob.name.split("/")[-1]),
                    blob.download_as_string(),
                    blob.content_type,
                )
                for blob in attachments_as_blobs
            ],
        )

        return Response()
