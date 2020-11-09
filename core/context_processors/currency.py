from core.currencies import CURRENT_CURRENCY_SYMBOL


def currency_code(request):
    return {"CURRENCY_SYMBOL": CURRENT_CURRENCY_SYMBOL}
