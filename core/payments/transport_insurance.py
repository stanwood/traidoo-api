from decimal import Decimal


def calculate_transport_insurance_rate(price: Decimal) -> Decimal:
    transport_insurance_rate = Decimal("0.06")

    if price <= 100:
        transport_insurance_rate = Decimal("0.15")
    elif 101 <= price <= 200:
        transport_insurance_rate = Decimal("0.12")
    elif 201 <= price <= 350:
        transport_insurance_rate = Decimal("0.10")
    elif 351 <= price <= 500:
        transport_insurance_rate = Decimal("0.08")
    elif 501 <= price <= 1000:
        transport_insurance_rate = Decimal("0.07")

    return transport_insurance_rate
