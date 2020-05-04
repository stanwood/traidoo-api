import environ
from split_settings.tools import include, optional

env = environ.Env()

include(
    "django/*.py",
    "project/*.py",
    "third_party/*.py",
    optional("environments/{}.py".format(env.str("GOOGLE_CLOUD_PROJECT", ""))),
)
