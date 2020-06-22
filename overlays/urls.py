from django.urls import path

from overlays.views import OverlayList

urlpatterns = [
    path("overlays", OverlayList.as_view(), name="overlays",),
]
