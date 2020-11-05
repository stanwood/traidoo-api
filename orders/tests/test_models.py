from decimal import Decimal

import pytest
from model_bakery import baker


def test_order_item_third_party_delivery_without_job(db, delivery_options, settings):
    settings.FEATURES["routes"] = True
    product = baker.make_recipe("products.product", delivery_options=delivery_options)
    order_item = baker.make_recipe(
        "orders.orderitem", delivery_option=delivery_options[1], product=product
    )
    assert not order_item.is_third_party_delivery


@pytest.mark.django_db
def test_order_item_third_party_delivery_without_user(delivery_options, settings):
    settings.FEATURES["routes"] = True
    product = baker.make_recipe("products.product", delivery_options=delivery_options)
    order_item = baker.make_recipe(
        "orders.orderitem", delivery_option=delivery_options[1], product=product
    )
    baker.make("jobs.Job", order_item=order_item)
    assert not order_item.is_third_party_delivery


@pytest.mark.django_db
def test_order_item_third_party_delivery(delivery_options, order_items, settings):
    settings.FEATURES["routes"] = True

    order_item = order_items[1]
    order_item.product.third_party_delivery = True
    order_item.product.save()

    baker.make("jobs.Job", order_item=order_item, user=baker.make("users.User"))

    assert order_item.is_third_party_delivery


@pytest.mark.django_db
def test_order_item_third_party_delivery_without_correct_delivery_option(settings):
    settings.FEATURES["routes"] = True

    delivery_option = baker.make_recipe("delivery_options.seller", id=1)
    product = baker.make_recipe("products.product", delivery_options=[delivery_option])
    order_item = baker.make_recipe(
        "orders.orderitem", delivery_option=delivery_option, product=product
    )
    user = baker.make("users.User")
    baker.make("jobs.Job", order_item=order_item, user=user)

    assert not order_item.is_third_party_delivery


@pytest.mark.django_db
def test_delivery_address_as_str_when_delivery_address_is_available():
    delivery_address = baker.make_recipe("delivery_addresses.delivery_address")
    delivery_option = baker.make_recipe("delivery_options.seller")
    product = baker.make_recipe("products.product", delivery_options=[delivery_option])
    order_item = baker.make(
        "orders.OrderItem",
        delivery_address=delivery_address,
        product=product,
        delivery_option=delivery_option,
    )

    assert (
        order_item.delivery_address_as_str
        == f"{delivery_address.company_name}, {delivery_address.street}, {delivery_address.zip}, {delivery_address.city}"
    )


@pytest.mark.django_db
def test_delivery_address_as_str_when_delivery_address_is_not_available():
    user = baker.make_recipe("users.user")
    order = baker.make("orders.Order", buyer=user)
    product = baker.make_recipe("products.product")
    order_item = baker.make(
        "orders.OrderItem",
        delivery_address=None,
        order=order,
        product=product,
        delivery_option=product.delivery_options.first(),
    )

    assert not order_item.delivery_address
    assert (
        order_item.delivery_address_as_str
        == f"{order_item.order.buyer.company_name}, {order_item.order.buyer.street}, {order_item.order.buyer.zip}, {order_item.order.buyer.city}"
    )


def test_order_platform_fee_share_with_local_platform_owner(
    db, order, order_items, buyer, traidoo_settings
):
    assert order.sum_of_seller_platform_fees.netto == 13.6
    assert order.local_platform_owner_platform_fee.netto == 8.16


def test_order_platform_fee_calculation_without_local_platform(
    db, order, traidoo_settings, order_items
):

    traidoo_settings.platform_user = None
    traidoo_settings.save()

    assert order.price_gross == 180.88


@pytest.mark.django_db
def test_get_delivery_company_third_party_withut_created_job(
    delivery_options, order_items, settings
):
    settings.FEATURES["routes"] = True

    order_item = order_items[1]
    order_item.product.third_party_delivery = True
    order_item.product.save()

    assert order_item.delivery_company == order_item.product.seller


@pytest.mark.django_db
def test_get_delivery_company_third_party_without_assigned_job(
    delivery_options, order_items, settings
):
    settings.FEATURES["routes"] = True

    order_item = order_items[1]
    order_item.product.third_party_delivery = True
    order_item.product.save()

    baker.make("jobs.Job", order_item=order_item, user=None)

    assert order_item.delivery_company == order_item.product.seller


def test_order_calc_items_do_not_include_seller_platform_fee_items(
    db, delivery_options, products
):
    buyer = baker.make_recipe("users.user", is_cooperative_member=True)
    order = baker.make_recipe("orders.order", buyer=buyer)
    baker.make_recipe(
        "orders.orderitem",
        delivery_option=delivery_options[0],
        product=products[0],
        order=order,
    )
    order.recalculate_items_delivery_fee()
    assert len(order.calc_items) == 3  # product, container deposit and logistics


def test_order_calc_items_include_buyer_platform_fee_item(
    db, delivery_options, products
):
    buyer = baker.make_recipe("users.user", is_cooperative_member=False)
    order = baker.make_recipe("orders.order", buyer=buyer)
    baker.make_recipe(
        "orders.orderitem",
        delivery_option=delivery_options[0],
        product=products[0],
        order=order,
    )
    order.recalculate_items_delivery_fee()
    assert (
        len(order.calc_items) == 4
    )  # product, container deposit, logistics and buyer platform fee


def test_order_calc_item_with_float_vat_rate(db, delivery_options, products):
    products[0].vat = 10.7
    products[0].save()
    buyer = baker.make_recipe("users.user", is_cooperative_member=True)
    order = baker.make_recipe("orders.order", buyer=buyer)
    baker.make_recipe(
        "orders.orderitem",
        delivery_option=delivery_options[0],
        product=products[0],
        order=order,
        quantity=10,
    )
    order.recalculate_items_delivery_fee()
    assert order.calc_items[0].vat == Decimal("10.7")
