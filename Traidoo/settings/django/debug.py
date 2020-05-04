import environ

env = environ.Env()

DEBUG = env.bool("DEBUG", False)
