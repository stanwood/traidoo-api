from decimal import Decimal

import environ

env = environ.Env()

CART_LIFESPAN = 60
UNVERIFIED_USER_LIFE_HOURS = 72
EARLIEST_DELIVERY_DATE_DAYS_RANGE = (1, 14)
NON_COOPERATIVE_MEMBERS_PLATFORM_FEE = Decimal(
    env("NON_COOPERATIVE_MEMBERS_PLATFORM_FEE", default="2.0", cast=str)
)
