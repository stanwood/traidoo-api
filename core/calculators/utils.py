from decimal import Decimal


def round_float(value):
    value = Decimal(str(value))
    value = value.quantize(Decimal(".01"), "ROUND_HALF_UP")
    return float(value)
