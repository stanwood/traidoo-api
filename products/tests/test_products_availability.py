import datetime

import pytest
from model_bakery import baker

from items.models import Item
from products.models import Product


@pytest.mark.django_db
def test_get_only_available_products(client_anonymous, traidoo_region):
    product_1 = baker.make(Product, region=traidoo_region)
    baker.make(Product, region=traidoo_region)

    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)

    baker.make(Item, quantity=1, product=product_1, latest_delivery_date=tomorrow)

    response = client_anonymous.get(f'/products?is_available=True')

    assert response.json()['count'] == 1
    assert response.json()['results'][0]['id'] == product_1.id


@pytest.mark.django_db
def test_do_not_return_products_when_quntity_is_0(client_anonymous, traidoo_region):
    product_1 = baker.make(Product, region=traidoo_region)
    baker.make(Product, region=traidoo_region)

    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)

    baker.make(Item, quantity=0, product=product_1, latest_delivery_date=tomorrow)

    response = client_anonymous.get(f'/products?is_available=True')

    assert response.json()['count'] == 0


@pytest.mark.django_db
def test_do_not_return_expired_products(client_anonymous, traidoo_region):
    product_1 = baker.make(Product, region=traidoo_region)
    baker.make(Product, region=traidoo_region)

    today = datetime.datetime.utcnow().date()

    baker.make(Item, quantity=1, product=product_1, latest_delivery_date=today)

    response = client_anonymous.get(f'/products?is_available=True')

    assert response.json()['count'] == 0


@pytest.mark.django_db
def test_get_only_not_available_products(client_anonymous, traidoo_region):
    product_1 = baker.make(Product, region=traidoo_region)
    product_2 = baker.make(Product, region=traidoo_region)

    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)

    baker.make(Item, quantity=1, product=product_1, latest_delivery_date=tomorrow)

    response = client_anonymous.get(f'/products?is_available=False')

    assert response.json()['count'] == 1
    assert response.json()['results'][0]['id'] == product_2.id


@pytest.mark.django_db
def test_get_all_products(client_anonymous, traidoo_region):
    product_1 = baker.make(Product, region=traidoo_region)
    baker.make(Product, region=traidoo_region)

    baker.make(Item, quantity=1, product=product_1)

    response = client_anonymous.get(f'/products')

    assert response.json()['count'] == 2


@pytest.mark.django_db
def test_do_not_count_expired_items(client_anonymous, traidoo_region):
    product = baker.make(Product, region=traidoo_region)

    today = datetime.datetime.utcnow().date()
    tomorrow = today + datetime.timedelta(days=1)
    yesterday = today - datetime.timedelta(days=1)

    baker.make(Item, quantity=1, product=product, latest_delivery_date=today)
    baker.make(Item, quantity=1, product=product, latest_delivery_date=yesterday)
    baker.make(Item, quantity=1, product=product, latest_delivery_date=tomorrow)

    response = client_anonymous.get(f'/products')

    assert response.json()['count'] == 1
    assert response.json()['results'][0]['itemsAvailable'] == 1
