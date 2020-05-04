import environ

env = environ.Env()

ADMINS = [admin.split(":") for admin in env.list("DJANGO_ADMINS")]
