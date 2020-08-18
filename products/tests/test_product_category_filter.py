import pytest
from model_bakery import baker

from products.models import Product


@pytest.mark.django_db
def test_get_products_by_category_with_subcategories(client_anonymous, traidoo_region):
    category_1 = baker.make_recipe("categories.category")
    category_2 = baker.make_recipe("categories.category", parent=category_1)
    category_3 = baker.make_recipe("categories.category", parent=category_1)

    baker.make(Product, category=category_1, region=traidoo_region)
    baker.make(Product, category=category_2, region=traidoo_region)
    baker.make(Product, category=category_3, region=traidoo_region)

    response = client_anonymous.get(f"/products?category__id={category_1.id}")

    assert response.json()["count"] == 3


@pytest.mark.django_db
def test_get_products_by_category_with_nested_subcategories(
    client_anonymous, traidoo_region
):
    category_1 = baker.make_recipe("categories.category")
    category_2 = baker.make_recipe("categories.category", parent=category_1)
    category_3 = baker.make_recipe("categories.category", parent=category_1)
    category_4 = baker.make_recipe("categories.category", parent=category_3)
    category_5 = baker.make_recipe("categories.category", parent=category_4)

    baker.make(Product, category=category_1, region=traidoo_region)
    baker.make(Product, category=category_2, region=traidoo_region)
    baker.make(Product, category=category_3, region=traidoo_region)
    baker.make(Product, category=category_4, region=traidoo_region)
    baker.make(Product, category=category_5, region=traidoo_region)

    response = client_anonymous.get(f"/products?category__id={category_1.id}")

    assert response.json()["count"] == Product.objects.count()
