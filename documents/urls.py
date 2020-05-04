# urls.py
from django.conf.urls import include, url

from .views import DocumentsTask

urlpatterns = [
    url(
        "queue/(?P<order_id>.+)/(?P<document_set>.+)",
        DocumentsTask.as_view(),
        name="task",
    )
]
