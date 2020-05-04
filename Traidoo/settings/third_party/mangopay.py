import environ

env = environ.Env()

MANGOPAY_URL = env("MANGOPAY_URL")
MANGOPAY_CLIENT_ID = env("MANGOPAY_CLIENT_ID")
