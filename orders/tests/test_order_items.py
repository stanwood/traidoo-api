import datetime

import pytest
import pytz
from freezegun import freeze_time
from model_mommy import mommy

from delivery_addresses.models import DeliveryAddress
from items.models import Item
from orders.models import Order, OrderItem
from products.models import Product

pytestmark = pytest.mark.django_db


def test_order_item_contains_delivery_address(client, buyer, seller, traidoo_region):
    client.force_authenticate(user=buyer)

    product = mommy.make(Product, seller=seller, region=traidoo_region)
    mommy.make(Item, product=product)
    order = mommy.make(Order, buyer=buyer)
    delivery_address = mommy.make(DeliveryAddress, user=buyer)
    mommy.make(
        OrderItem, product=product, order=order, delivery_address=delivery_address
    )

    response = client.get(f"/orders/{order.id}/items")

    delivery_adress_response = response.json()["results"][0]["deliveryAddress"]
    assert delivery_adress_response["city"] == delivery_address.city
    assert delivery_adress_response["companyName"] == delivery_address.company_name
    assert delivery_adress_response["id"] == delivery_address.id
    assert delivery_adress_response["street"] == delivery_address.street
    assert delivery_adress_response["zip"] == delivery_address.zip


def test_merge_order_items_by_product(client, buyer, seller, delivery_options):
    client.force_authenticate(user=buyer)

    product = mommy.make_recipe("products.product", seller=seller)
    product_2 = mommy.make_recipe("products.product", seller=seller)
    mommy.make(Item, product=product)
    mommy.make(Item, product=product_2)
    order = mommy.make(Order, buyer=buyer)
    delivery_address = mommy.make(DeliveryAddress, user=buyer)
    mommy.make(
        OrderItem,
        product=product,
        order=order,
        delivery_address=delivery_address,
        latest_delivery_date="2019-01-01",
        delivery_option=delivery_options[0],
        quantity=1,
    )
    mommy.make(
        OrderItem,
        product=product,
        order=order,
        delivery_address=delivery_address,
        latest_delivery_date="2019-01-02",
        delivery_option=delivery_options[0],
        quantity=1,
    )
    mommy.make(
        OrderItem,
        product=product_2,
        order=order,
        delivery_address=delivery_address,
        latest_delivery_date="2019-01-02",
        delivery_option=delivery_options[0],
        quantity=1,
    )

    response = client.get(f"/orders/{order.id}/items")

    assert (
        response.json()["count"] == 3
    )  # TODO: incorrect value (intentionally), check the view

    results = response.json()["results"]
    assert len(results) == 2

    quantity_results = dict(
        (item["product"]["id"], item["quantity"]) for item in response.json()["results"]
    )

    assert quantity_results.get(product.id) == 2
    assert quantity_results.get(product_2.id) == 1


def test_seller_can_get_order_items_for_own_order(client_seller, seller, products):
    order = mommy.make(Order, buyer=seller)
    order_item_1 = mommy.make_recipe(
        "orders.orderitem", order=order, product=products[0]
    )
    order_item_2 = mommy.make_recipe(
        "orders.orderitem", order=order, product=products[1]
    )
    response = client_seller.get(f"/orders/{order.id}/items")
    assert response.json()["count"] == 2
    assert set([item["id"] for item in response.json()["results"]]) == {
        order_item_1.id,
        order_item_2.id,
    }


@freeze_time("2019-04-10 09:59:59")  # UTC, check OrderItem.delivery_date()
def test_delivery_date_before_12():
    order = mommy.make_recipe(
        "orders.order", earliest_delivery_date=datetime.datetime.today()
    )
    order_item = mommy.make_recipe("orders.orderitem", order=order)
    assert order_item.delivery_date.isoformat() == "2019-04-11"


@freeze_time("2019-04-10 10:00:01")  # UTC, check OrderItem.delivery_date()
def test_delivery_date_after_12():
    order = mommy.make_recipe(
        "orders.order", earliest_delivery_date=datetime.datetime.today()
    )
    order_item = mommy.make_recipe("orders.orderitem", order=order)
    assert order_item.delivery_date.isoformat() == "2019-04-12"


@freeze_time("2019-04-12 10:00:01")  # UTC, check OrderItem.delivery_date()
def test_delivery_date_order_on_friday():
    order = mommy.make_recipe(
        "orders.order", earliest_delivery_date=datetime.datetime.today()
    )
    order_item = mommy.make_recipe("orders.orderitem", order=order)
    assert order_item.delivery_date.isoformat() == "2019-04-15"


def test_delivery_date_order_on_weekend():
    with freeze_time("2019-04-13 10:00:01"):  # UTC, check OrderItem.delivery_date()
        order = mommy.make_recipe(
            "orders.order", earliest_delivery_date=datetime.datetime.today()
        )
        order_item = mommy.make_recipe("orders.orderitem", order=order)
        assert order_item.delivery_date.isoformat() == "2019-04-16"


def test_delivery_date_when_earliest_delivery_date_later_than_created():
    with freeze_time("2019-07-15 12:11"):
        order_item = mommy.make_recipe("orders.orderitem")
        order = order_item.order
        order.earliest_delivery_date = datetime.datetime(
            2019, 7, 16, 12, 11, tzinfo=pytz.timezone("CET")
        )
        order.save()
        order.recalculate_items_delivery_fee()
        assert order_item.delivery_date.isoformat() == "2019-07-17"
