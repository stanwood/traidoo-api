from typing import Union

from rest_framework.request import Request

from .models import Region


def get_region(request: Request) -> Union[Region, None]:
    """
    Base on header in HTTP request get a valid region or None incase
    header is not provided or region with value provided in the headers
    does not exists.
    """
    region_slug = request.headers.get("Region") or request.META.get("HTTP_REGION")

    if not region_slug:
        return None

    try:
        region = Region.objects.prefetch_related(
            "settings", "settings__platform_user", "settings__logistics_company"
        ).get(slug=region_slug)
    except Region.DoesNotExist:
        region = None

    return region
