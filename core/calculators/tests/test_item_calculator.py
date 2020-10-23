from decimal import Decimal

import pytest
from model_bakery import baker

from delivery_options.models import DeliveryOption


@pytest.fixture
def central_logistic_order_items(db):
    central_delivery_option = baker.make_recipe("delivery_options.central_logistic")
    region = baker.make_recipe("common.region")
    order = baker.make_recipe("orders.order")
    order.buyer.region = region
    order.buyer.save()
    product_1 = baker.make_recipe(
        "products.product",
        price=100,
        amount=1,
        vat=10.7,
        delivery_options=[central_delivery_option],
    )
    product_2 = baker.make_recipe(
        "products.product",
        price=50,
        amount=1,
        vat=10.7,
        delivery_options=[central_delivery_option],
    )
    item_1 = baker.make_recipe(
        "orders.orderitem",
        order=order,
        product=product_1,
        quantity=1,
        delivery_option=central_delivery_option,
    )
    item_2 = baker.make_recipe(
        "orders.orderitem",
        order=order,
        product=product_2,
        quantity=1,
        delivery_option=central_delivery_option,
    )

    return item_1, item_2


@pytest.fixture
def central_logistic_cart_items(db):
    central_delivery_option = baker.make_recipe("delivery_options.central_logistic")
    product_1 = baker.make_recipe(
        "products.product",
        price=100,
        amount=1,
        vat=10.7,
        delivery_options=[central_delivery_option],
    )
    product_2 = baker.make_recipe(
        "products.product",
        price=50,
        amount=1,
        vat=10.7,
        delivery_options=[central_delivery_option],
    )

    region = baker.make_recipe("common.region")
    cart = baker.make_recipe("carts.cart")
    cart.user.region = region
    cart.user.save()

    item_1 = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        product=product_1,
        quantity=1,
        delivery_option=central_delivery_option,
    )
    item_2 = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        product=product_2,
        quantity=1,
        delivery_option=central_delivery_option,
    )

    return item_1, item_2


def test_item_calculations(db, order_items):

    assert order_items[0].price.netto == 95.4
    assert order_items[0].price_gross == 113.53
    assert order_items[0].container_deposit.netto == 3.2


def test_calculate_central_delivery_fee_cart_items(central_logistic_cart_items):
    item_1, item_2 = central_logistic_cart_items
    assert item_1.transport_insurance == Decimal("12")
    assert item_2.transport_insurance == Decimal("6")
    assert item_1._delivery_fee().netto == Decimal("12")
    assert item_2._delivery_fee().netto == Decimal("6")


def test_calculate_central_delivery_fee_order_items(central_logistic_order_items):
    item_1, item_2 = central_logistic_order_items
    assert item_1.transport_insurance == Decimal("12")
    assert item_2.transport_insurance == Decimal("6")
    assert item_1._delivery_fee().netto == Decimal("12")
    assert item_2._delivery_fee().netto == Decimal("6")
