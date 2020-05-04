import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env()

environment = env.get_value("GOOGLE_CLOUD_PROJECT", default=None)
sentry_dsn = env.get_value("SENTRY_DSN", default=None)

if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[DjangoIntegration()],
        environment=environment,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )
