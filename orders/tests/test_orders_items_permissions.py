import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy

from items.models import Item
from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()


@pytest.fixture
def _create_test_data(buyer, seller, seller_group, buyer_group, traidoo_region):
    product = mommy.make(Product, seller=seller, region=traidoo_region)
    mommy.make(Item, product=product)
    order = mommy.make(Order, buyer=buyer)
    order_item = mommy.make_recipe("orders.orderitem", product=product, order=order)
    yield product, order, order_item


@pytest.mark.django_db
def test_get_orders_items_by_buyer(client, buyer, _create_test_data):
    client.force_authenticate(user=buyer)

    response = client.get(f"/orders/{_create_test_data[1].id}/items")
    assert Order.objects.count() == 1
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == _create_test_data[2].id


@pytest.mark.django_db
def test_get_orders_items_by_other_buyer(client, buyer, buyer_group, _create_test_data):
    buyer_2 = mommy.make(User, groups=[buyer_group])

    client.force_authenticate(user=buyer_2)

    response = client.get(f"/orders/{_create_test_data[1].id}/items")
    assert Order.objects.count() == 1
    assert response.json()["count"] == 0
