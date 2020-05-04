import datetime

import pytest
from model_mommy import mommy

from carts.models import CartItem


@pytest.mark.django_db
def test_add_product_to_cart(client_buyer, traidoo_region):
    product_item = mommy.make_recipe("items.item", quantity=10)

    response = client_buyer.post(
        "/cart", {"productId": product_item.product.id, "quantity": 1}
    )

    assert response.status_code == 200
    assert response.json() == {"notAvailable": 0}

    product_item.refresh_from_db()
    assert product_item.quantity == 9

    assert CartItem.objects.count() == 1
    assert (
        CartItem.objects.first().delivery_option.id
        == product_item.product.delivery_options.first().id
    )


@pytest.mark.django_db
def test_add_product_to_cart_from_multiple_product_items(client_buyer, traidoo_region):
    product_item_1 = mommy.make_recipe(
        "items.item",
        quantity=2,
        latest_delivery_date=datetime.datetime.now() + datetime.timedelta(days=2),
    )
    product_item_2 = mommy.make_recipe(
        "items.item",
        product=product_item_1.product,
        quantity=4,
        latest_delivery_date=datetime.datetime.now() + datetime.timedelta(days=1),
    )

    response = client_buyer.post(
        "/cart", {"productId": product_item_1.product.id, "quantity": 5}
    )

    assert response.status_code == 200
    assert response.json() == {"notAvailable": 0}

    product_item_2.refresh_from_db()
    assert product_item_2.quantity == 0
    product_item_1.refresh_from_db()
    assert product_item_1.quantity == 1


@pytest.mark.django_db
def test_add_product_to_cart_with_disabled_central_logistic(
    client_buyer, traidoo_region
):
    product_item = mommy.make_recipe("items.item", quantity=10)

    region_settings = product_item.product.region.settings.first()
    region_settings.central_logistics_company = False
    region_settings.save()
    region_settings.refresh_from_db()

    response = client_buyer.post(
        "/cart", {"productId": product_item.product.id, "quantity": 1}
    )

    assert response.status_code == 200
    assert response.json() == {"notAvailable": 0}

    product_item.refresh_from_db()
    assert product_item.quantity == 9

    assert CartItem.objects.count() == 1
    assert (
        CartItem.objects.first().delivery_option.id
        == product_item.product.first_available_delivery_option().id
    )
