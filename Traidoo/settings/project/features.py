import environ

env = environ.Env()

FEATURES = {
    "routes": env.bool("FEATURE_ROUTE"),
    "delivery_date": env.bool("FEATURE_DELIVERY_DATE"),
}
