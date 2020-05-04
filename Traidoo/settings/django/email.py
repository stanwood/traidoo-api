import environ

env = environ.Env()

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
    "MAILGUN_API_URL": env("MAILGUN_API_URL"),
}

INTERCOM_EMAIL = env.str("INTERCOM_EMAIL", None)
