from django.urls import reverse

from common.utils import get_region
from core.errors.exceptions import RegionHeaderMissingException


def region_middleware(get_response):
    def middleware(request):
        if request.META.get("HTTP_X_APPENGINE_CRON") or request.META.get(
            "HTTP_X_APPENGINE_QUEUENAME"
        ):
            return get_response(request)

        if not (
            request.path.startswith(reverse("admin:index"))
            or request.path.startswith(reverse("webhook"))
            or request.path.startswith("/_ah/warmup")
            or get_region(request)
        ):
            raise RegionHeaderMissingException()

        return get_response(request)

    return middleware
