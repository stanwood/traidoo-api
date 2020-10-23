import pytest
from model_bakery import baker

pytestmark = pytest.mark.django_db


def test_get_products_list_avilable_items(client_seller, seller, traidoo_region):
    region_1, region_2 = baker.make_recipe("common.region", _quantity=2)
    product = baker.make_recipe(
        "products.product", seller=seller, regions=[traidoo_region, region_1, region_2]
    )
    baker.make_recipe("items.item", quantity=2, product=product)
    response = client_seller.get("/products?limit=10&ordering=-created_at&my=true")

    assert response.json()["results"][0]["itemsAvailable"] == 2
