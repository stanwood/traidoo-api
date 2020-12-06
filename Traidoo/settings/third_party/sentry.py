from core.errors.exceptions import RegionHeaderMissingException
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env()

environment = env.get_value("GOOGLE_CLOUD_PROJECT", default=None)
sentry_dsn = env.get_value("SENTRY_DSN", default=None)

if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        ignore_errors=[RegionHeaderMissingException],
        integrations=[DjangoIntegration()],
        environment=environment,
        send_default_pii=True,
    )
