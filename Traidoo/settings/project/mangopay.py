import environ

env = environ.Env()
MANGOPAY_PASSWORD = env("MANGOPAY_PASSWORD")
