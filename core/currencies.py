from django.conf import settings

CURRENCIES = {
    "EUR": {"code": "EUR", "symbol": "€",},
    "CHF": {"code": "CHF", "symbol": "CHF",},
}

CURRENT_CURRENCY_CODE = CURRENCIES[settings.CURRENCY_CODE]["code"]
CURRENT_CURRENCY_SYMBOL = CURRENCIES[settings.CURRENCY_CODE]["symbol"]
