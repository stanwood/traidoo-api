import environ

env = environ.Env()


CACHEOPS_REDIS = {
    "host": env("REDIS_HOST"),
    "port": env("REDIS_PORT"),
    # "db": 1,
    "socket_timeout": 2,
    "password": env("REDIS_PASSWORD"),
}

CACHEOPS = {
    "carts.*": {"ops": "all", "timeout": 60 * 60},
    "categories.*": {"ops": "all", "timeout": 60 * 60},
    "checkout.*": {"ops": "all", "timeout": 60 * 60},
    "common.*": {"ops": "all", "timeout": 60 * 60},
    "containers.*": {"ops": "all", "timeout": 60 * 60},
    "delivery_addresses.*": {"ops": "all", "timeout": 60 * 60},
    "delivery_options.*": {"ops": "all", "timeout": 60 * 60},
    "documents.*": {"ops": "all", "timeout": 60 * 60},
    "groups.*": {"ops": "all", "timeout": 60 * 60},
    "items.*": {"ops": "all", "timeout": 60 * 60},
    "jobs.*": {"ops": "all", "timeout": 60 * 60},
    "orders.*": {"ops": "all", "timeout": 60 * 60},
    "overlays.*": {"ops": "all", "timeout": 60 * 60},
    "payments.*": {"ops": "all", "timeout": 60 * 60},
    "products.*": {"ops": "all", "timeout": 60 * 60},
    "routes.*": {"ops": "all", "timeout": 60 * 60},
    "sellers.*": {"ops": "all", "timeout": 60 * 60},
    "settings.*": {"ops": "all", "timeout": 60 * 60},
    "tags.*": {"ops": "all", "timeout": 60 * 60},
}

CACHEOPS_DEGRADE_ON_FAILURE = True
