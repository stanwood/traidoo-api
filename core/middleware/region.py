import re

from http import HTTPStatus

from django.http.response import JsonResponse
from django.urls import reverse


from common.utils import get_region

ADMIN_REQUEST_RE = re.compile(r"/[a-z]{2}/admin")


def is_admin_request(request):

    return bool(ADMIN_REQUEST_RE.findall(request.path)) or bool(
        ADMIN_REQUEST_RE.findall(request.META.get("HTTP_REFERER", ""))
    )


def is_task_queue_or_cron(request):
    return request.META.get("HTTP_X_APPENGINE_CRON") or request.META.get(
        "HTTP_X_APPENGINE_QUEUENAME"
    )


def region_middleware(get_response):
    def middleware(request):

        region = get_region(request)

        if not (
            is_task_queue_or_cron(request)
            or is_admin_request(request)
            or request.path.startswith(reverse("webhook"))
            or request.path.startswith("/_ah/warmup")
            or request.path in ("/favicon.ico", "/robots.txt")
            or region
        ):
            return JsonResponse(
                {
                    "message": "Could not satisfy the request Region header.",
                    "code": "not_acceptable",
                },
                status=HTTPStatus.NOT_ACCEPTABLE,
            )

        request.region = region

        return get_response(request)

    return middleware
