import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy

from items.models import Item
from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()


@pytest.fixture
def _create_test_data(buyer, seller, seller_group, buyer_group, traidoo_region):
    seller_2 = mommy.make(User, groups=[seller_group])
    buyer_2 = mommy.make(User, groups=[buyer_group])

    product_1 = mommy.make(Product, seller=seller_2, region=traidoo_region)
    product_2 = mommy.make(Product, seller=seller, region=traidoo_region)

    mommy.make(Item, product=product_1)
    mommy.make(Item, product=product_2)

    order_1 = mommy.make(Order, buyer=buyer)
    order_2 = mommy.make(Order, buyer=buyer_2)

    mommy.make_recipe("orders.orderitem", product=product_1, order=order_1)
    mommy.make_recipe("orders.orderitem", product=product_2, order=order_2)

    yield (product_1, product_2), (order_1, order_2)


@pytest.mark.django_db
def test_get_orders_admin(client_admin, _create_test_data):
    response = client_admin.get("/orders")
    assert Order.objects.count() == 2
    assert response.json()["count"] == 2


@pytest.mark.django_db
def test_get_orders_buyer(client_buyer, _create_test_data):
    response = client_buyer.get("/orders")
    assert Order.objects.count() == 2
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == _create_test_data[1][0].id


@pytest.mark.django_db
def test_seller_cannot_see_other_orders(client_seller, _create_test_data, seller):
    response = client_seller.get("/orders")
    assert Order.objects.count() == 2
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_seller_can_get_own_order(client_seller, seller):
    order = mommy.make(Order, buyer=seller)
    response = client_seller.get(f"/orders/{order.id}")
    assert response.json()["id"] == order.id


@pytest.mark.django_db
def test_seller_can_get_own_order_with_multiple_items(client_seller, seller):
    order = mommy.make(Order, buyer=seller)
    mommy.make_recipe("orders.orderitem", order=order)
    mommy.make_recipe("orders.orderitem", order=order)
    response = client_seller.get(f"/orders/{order.id}")
    assert response.json()["id"] == order.id
    assert len(response.json()["items"]) == 2


@pytest.mark.django_db
def test_admin_can_get_order(client_admin, seller):
    order = mommy.make(Order, buyer=seller)
    mommy.make_recipe("orders.orderitem", order=order)
    mommy.make_recipe("orders.orderitem", order=order)
    response = client_admin.get(f"/orders/{order.id}")
    assert response.json()["id"] == order.id
    assert len(response.json()["items"]) == 2
