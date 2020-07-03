from django.conf.urls import include, url

from .tasks.documents import DocumentsTask
from .views.download import DownloadDocument

urlpatterns = [
    url("(?P<document_id>.+)/download", DownloadDocument.as_view()),
    url(
        "queue/(?P<order_id>.+)/(?P<document_set>.+)",
        DocumentsTask.as_view(),
        name="task",
    ),
]
