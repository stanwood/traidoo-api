import datetime

import pytest
from model_bakery import baker

from categories.models import Category
from items.models import Item
from products.models import Product


@pytest.mark.django_db
def test_return_category_with_products(client_anonymous, traidoo_region):
    category_1 = baker.make(Category)
    product_1 = baker.make(Product, category=category_1, region=traidoo_region)
    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)
    baker.make(Item, product=product_1, quantity=2, latest_delivery_date=tomorrow)
    response = client_anonymous.get(f"/categories")
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == category_1.id


@pytest.mark.django_db
def test_do_not_return_category_with_quantity_0(client_anonymous, traidoo_region):
    category_1 = baker.make(Category)
    product_1 = baker.make(Product, category=category_1, region=traidoo_region)
    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)
    baker.make(Item, product=product_1, quantity=0, latest_delivery_date=tomorrow)
    response = client_anonymous.get(f"/categories?has_products=true")
    assert len(response.json()) == 0


@pytest.mark.django_db
def test_do_not_return_category_with_expired_item(client_anonymous, traidoo_region):
    category_1 = baker.make(Category)

    product_1 = baker.make(Product, category=category_1, region=traidoo_region)

    today = datetime.datetime.utcnow().date()

    baker.make(Item, product=product_1, quantity=5, latest_delivery_date=today)

    response = client_anonymous.get(f"/categories?has_products=true")

    assert len(response.json()) == 0


@pytest.mark.django_db
def test_return_all_categories(client_anonymous, traidoo_region):
    category = baker.make(Category)
    product = baker.make(Product, category=category, region=traidoo_region)
    today = datetime.datetime.utcnow().date()
    baker.make(Item, product=product, quantity=5, latest_delivery_date=today)

    baker.make(Category, _quantity=4)
    response = client_anonymous.get(f"/categories")
    assert len(response.json()) == 5
    response = client_anonymous.get(f"/categories?has_products=false")
    assert len(response.json()) == 5


@pytest.mark.django_db
def test_return_category_when_subcategory_has_products(
    client_anonymous, traidoo_region
):
    category_1 = baker.make(Category)
    category_2 = baker.make(Category, parent=category_1)

    product_1 = baker.make(Product, category=category_2, region=traidoo_region)

    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)

    baker.make(Item, product=product_1, quantity=5, latest_delivery_date=tomorrow)

    response = client_anonymous.get(f"/categories?has_products=true")

    assert len(response.json()) == 2


@pytest.mark.django_db
def test_return_categories_when_subcategory_has_products(
    client_anonymous, traidoo_region
):
    category_1 = baker.make(Category)
    category_2 = baker.make(Category, parent=category_1)
    category_3 = baker.make(Category, parent=category_2)
    category_4 = baker.make(Category, parent=category_3)

    product_1 = baker.make(Product, category=category_4, region=traidoo_region)

    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)

    baker.make(Item, product=product_1, quantity=5, latest_delivery_date=tomorrow)

    response = client_anonymous.get(f"/categories?has_products=true")

    assert len(response.json()) == 4
