import environ

env = environ.Env()

CURRENCY_CODE = env("CURRENCY")
