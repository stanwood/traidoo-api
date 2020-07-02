from decimal import Decimal

from model_bakery import baker

from delivery_options.models import DeliveryOption


def test_item_calculations(db, order_items):

    assert order_items[0].price.netto == 95.4
    assert order_items[0].price_gross == 113.53
    assert order_items[0].container_deposit.netto == 3.2
    assert order_items[0]._delivery_fee().netto == 15.81


def test_calculate_transport_insurance(db):
    product = baker.make_recipe("products.product", price=31.9, amount=1, vat=10.7)
    item = baker.make_recipe(
        "orders.orderitem",
        product=product,
        quantity=1,
        delivery_option_id=DeliveryOption.CENTRAL_LOGISTICS,
    )
    assert item.transport_insurance == Decimal("4.79")
