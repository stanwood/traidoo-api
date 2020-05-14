import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_mommy import mommy

from containers.models import Container
from orders.models import Order, OrderItem
from products.models import Product

from ...factories import BuyerPlatformInvoiceFactory

User = get_user_model()


@pytest.mark.parametrize(
    "is_cooperative_member,expected_value", [(True, 0.0), (False, 1.91)]
)
@pytest.mark.django_db
def test_platform_invoice_factory_buyer_invoice_data_available(
    is_cooperative_member,
    expected_value,
    seller,
    central_platform_user,
    logistics_user,
    buyer_group,
    traidoo_settings,
    product,
    delivery_address,
    delivery_options,
    faker,
    traidoo_region,
):
    buyer = mommy.make(
        User,
        company_name="This is useless company name",
        email="thisisuselessemailofthecompany@example.com",
        invoice_email="thisisuselessemailofthecompany+invoice@example.com",
        phone="987654321",
        groups=[buyer_group],
        is_cooperative_member=is_cooperative_member,
        region=traidoo_region,
    )

    assert buyer.is_cooperative_member is is_cooperative_member

    product = mommy.make(
        Product,
        seller=seller,
        price=10.6,
        amount=3,
        vat=19,
        container_type=mommy.make(Container, deposit=3.2),
        region=traidoo_region,
    )

    order = mommy.make(Order, buyer=buyer, region=traidoo_region)

    mommy.make(
        OrderItem,
        product=product,
        quantity=3,
        order=order,
        delivery_address=delivery_address,
        delivery_option=delivery_options[0],
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
    )

    factory = BuyerPlatformInvoiceFactory(order, region=traidoo_region)

    # Only one line on this invoice
    assert len(factory.lines) == 1

    invoice_line = factory.lines[0]

    assert invoice_line == {
        "number": "",
        "name": u"Plattformgebühr",
        "producer": central_platform_user.company_name,
        "price": expected_value,
        "unit": "",
        "count": 1,
        "vat_rate": float(traidoo_settings.platform_fee_vat),
        "amount": 1.0,
        "category": "",
        "seller_user_id": central_platform_user.id,
    }

    assert factory.buyer == factory.as_company(buyer)
