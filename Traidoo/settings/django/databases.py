import environ

env = environ.Env()


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": env("POSTGRESQL_USER"),
        "PASSWORD": env("POSTGRESQL_PASSWORD"),
        "PORT": env("POSTGRESQL_PORT", default=5432),
        "NAME": env("POSTGRESQL_NAME"),
        "HOST": env("POSTGRESQL_HOST"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 60,
    }
}
