import re

from django.urls import reverse

from common.utils import get_region
from core.errors.exceptions import RegionHeaderMissingException


def region_middleware(get_response):
    def middleware(request):
        if request.META.get("HTTP_X_APPENGINE_CRON") or request.META.get(
            "HTTP_X_APPENGINE_QUEUENAME"
        ):
            return get_response(request)

        admin_request = bool(re.match(r"^/[a-z]{2}/admin", request.path))

        if not (
            admin_request
            or request.path.startswith(reverse("webhook"))
            or request.path.startswith("/_ah/warmup")
            or request.path in ("/favicon.ico", "/robots.txt")
            or get_region(request)
        ):
            raise RegionHeaderMissingException()

        return get_response(request)

    return middleware
