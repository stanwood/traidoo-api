from django.conf.urls import url

from .tasks.documents import DocumentsTask
from .tasks.mails import MailDocumentsTask
from .views.download import DownloadDocument

urlpatterns = [
    url(
        "(?P<document_id>.+)/download",
        DownloadDocument.as_view(),
        name="download-document",
    ),
    url(
        "queue/(?P<order_id>.+)/(?P<document_set>.+)",
        DocumentsTask.as_view(),
        name="task",
    ),
    url(
        r"mail/(?P<order_id>\d+)/(?P<email>.+)",
        MailDocumentsTask.as_view(),
        name="mail-documents",
    ),
]
