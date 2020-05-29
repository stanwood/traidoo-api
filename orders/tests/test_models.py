import pytest
from model_mommy import mommy


@pytest.mark.django_db
def test_order_item_third_party_delivery_without_job(delivery_options):
    order_item = mommy.make_recipe(
        "orders.orderitem", delivery_option=delivery_options[1]
    )
    assert not order_item.is_third_party_delivery


@pytest.mark.django_db
def test_order_item_third_party_delivery_without_user(delivery_options):
    order_item = mommy.make_recipe(
        "orders.orderitem", delivery_option=delivery_options[1]
    )
    mommy.make("jobs.Job", order_item=order_item)
    assert not order_item.is_third_party_delivery


@pytest.mark.django_db
def test_order_item_third_party_delivery(delivery_options, order_items, settings):
    settings.FEATURES["routes"] = True

    order_item = order_items[1]
    order_item.product.third_party_delivery = True
    order_item.product.save()

    mommy.make("jobs.Job", order_item=order_item, user=mommy.make("users.User"))

    assert order_item.is_third_party_delivery


@pytest.mark.django_db
def test_order_item_third_party_delivery_without_correct_delivery_option(
    delivery_options,
):
    order_item = mommy.make_recipe(
        "orders.orderitem", delivery_option=delivery_options[0]
    )
    user = mommy.make("users.User")
    mommy.make("jobs.Job", order_item=order_item, user=user)

    assert not order_item.is_third_party_delivery


@pytest.mark.django_db
def test_delivery_address_as_str_when_delivery_address_is_available():
    delivery_address = mommy.make_recipe("delivery_addresses.delivery_address")
    product = mommy.make_recipe("products.product")
    order_item = mommy.make(
        "orders.OrderItem", delivery_address=delivery_address, product=product
    )

    assert (
        order_item.delivery_address_as_str
        == f"{delivery_address.company_name}, {delivery_address.street}, {delivery_address.zip}, {delivery_address.city}"
    )


@pytest.mark.django_db
def test_delivery_address_as_str_when_delivery_address_is_not_available():
    user = mommy.make_recipe("users.user")
    order = mommy.make("orders.Order", buyer=user)
    product = mommy.make_recipe("products.product")
    order_item = mommy.make(
        "orders.OrderItem", delivery_address=None, order=order, product=product
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

    assert order.price_gross == 197.06
