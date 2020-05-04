import environ

env = environ.Env()

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 10,
    "MAX_PAGE_SIZE": 100,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]
    if env.bool("DEBUG")
    else ["djangorestframework_camel_case.render.CamelCaseJSONRenderer",],
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
    ),
    "JSON_UNDERSCOREIZE": {"no_underscore_before_number": True},
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "COERCE_DECIMAL_TO_STRING": False,
    "DATETIME_FORMAT": None,
    "EXCEPTION_HANDLER": "core.errors.exception_handler.full_details_exception_handler",
}
