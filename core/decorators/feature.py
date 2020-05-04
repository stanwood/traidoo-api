from functools import wraps

from django.conf import settings
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def require_feature(feature_name):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if settings.FEATURES.get(feature_name, None) == False:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return func(request, *args, **kwargs)

        return inner

    return decorator
