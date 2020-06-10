import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy

from documents import factories
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
def test_get_order_anonymous(api_client):
    response = api_client.get("/orders/1")
    assert response.status_code == 401


@pytest.mark.django_db
def test_buyer_can_get_own_order_with_multiple_items(api_client):
    region = mommy.make_recipe("common.region")
    mommy.make_recipe("settings.setting", region=region)
    seller = mommy.make_recipe("users.user", region=region)
    buyer = mommy.make_recipe("users.user", region=region)
    product_1 = mommy.make_recipe("products.product", seller=seller, region=region)
    product_2 = mommy.make_recipe(
        "products.product",
        seller=seller,
        region=region,
        # weird that mommy tries to make an update on existing delivery options without this line
        delivery_options=product_1.delivery_options.all(),
    )
    order = mommy.make_recipe("orders.order", buyer=buyer, region=region, total_price=1)
    mommy.make_recipe(
        "orders.orderitem",
        order=order,
        product=product_1,
        delivery_option=product_1.delivery_options.first(),
    )
    mommy.make_recipe(
        "orders.orderitem",
        order=order,
        product=product_2,
        delivery_option=product_2.delivery_options.first(),
    )

    factory = factories.OrderConfirmationBuyerFactory(order, region, seller)
    document = factory.compose()
    document.save()

    api_client.force_authenticate(buyer)

    response = api_client.get(f"/orders/{order.id}")

    response_json = response.json()
    assert response_json["id"] == order.id
    assert response_json["status"] == order.status
    assert len(response.json()["products"]) == 2
    assert len(response.json()["deposits"]) == 2
    assert len(response.json()["platforms"]) == 1
    assert len(response.json()["logistics"]) == 0
