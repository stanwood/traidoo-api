import environ

env = environ.Env()

FEATURES = {
    "routes": env.bool("FEATURE_ROUTE"),
    "delivery_date": env.bool("FEATURE_DELIVERY_DATE"),
    "company_registration_id": env.bool("FEATURE_COMPANY_REGISTRATION_ID"),
}
