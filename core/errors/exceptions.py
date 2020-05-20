from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_406_NOT_ACCEPTABLE
from django.utils.translation import gettext_lazy as _


class ProtectedEntityException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = _("Cannot be deleted due to protected related entities.")
    default_code = "protected_error"


class RegionHeaderMissingException(APIException):
    status_code = HTTP_406_NOT_ACCEPTABLE
    default_detail = _("Could not satisfy the request Region header.")
    default_code = "not_acceptable"
