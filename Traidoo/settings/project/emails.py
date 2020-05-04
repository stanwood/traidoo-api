import environ

env = environ.Env()


LOGISTICS_EMAIL = env("LOGISTICS_EMAIL")  # TODO: remove it, it's not required
PLATFORM_EMAIL = SERVER_EMAIL = env(
    "PLATFORM_EMAIL"
)  # TODO: remove it, it's not required
REAL_ADMINS = env.tuple("REAL_ADMINS")
