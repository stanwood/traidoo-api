import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from categories.models import Category
from items.models import Item
from products.models import Product

pytestmark = pytest.mark.django_db()


@freeze_time("2019-01-01")
def test_items_available_calculation(client_buyer, product, delivery_options):
    category_1 = baker.make(Category, name="Foo")
    category_2 = baker.make(Category, name="Foo", parent=category_1)

    product.name = "Foo"
    product.description = "Foo"
    product.image_url = "Foo"
    product.tags.add("Foo")
    product.tags.add("tag-a")
    product.tags.add("tag-b")
    product.tags.add("tag-c")
    product.category = category_1
    product.delivery_options.set(delivery_options)
    product.seller.first_name = "Foo"
    product.seller.last_name = "Foo"
    product.seller.company_name = "Foo"
    product.seller.save()
    product.save()
    baker.make(
        Item,
        product=product,
        quantity=3,
        latest_delivery_date=datetime.date(2019, 2, 1),
    )

    response = client_buyer.get(f"/products/{product.id}")
    assert response.data["items_available"] == 3

    search = client_buyer.get(
        f"/products",
        data={"search": "Foo", "offset": 0, "limit": 10, "is_available": True},
    )
    assert search.data["results"][0]["items_available"] == 3
