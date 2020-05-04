from decimal import Decimal


def calculate_transport_insurance(price: Decimal) -> Decimal:
    delivery_fee = 0.06

    if price <= 100:
        delivery_fee = 0.15
    elif 101 <= price <= 200:
        delivery_fee = 0.12
    elif 201 <= price <= 350:
        delivery_fee = 0.10
    elif 351 <= price <= 500:
        delivery_fee = 0.08
    elif 501 <= price <= 1000:
        delivery_fee = 0.07

    return Decimal(delivery_fee)
