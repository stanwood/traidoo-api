import datetime

import pytest
from model_mommy import mommy

from carts.models import CartItem
from items.models import Item


@pytest.mark.django_db
def test_remove_product_from_cart(buyer, client_buyer, traidoo_region):
    product_item = mommy.make_recipe("items.item", quantity=9)
    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item.product,
        latest_delivery_date=product_item.latest_delivery_date,
    )

    response = client_buyer.delete(f"/cart/{product_item.product.id}")

    assert response.status_code == 204

    product_item.refresh_from_db()
    assert product_item.quantity == 10

    with pytest.raises(CartItem.DoesNotExist):
        cart_item.refresh_from_db()


@pytest.mark.django_db
def test_remove_product_from_cart_and_release_all_product_items(
    buyer, client_buyer, traidoo_region
):
    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(days=2)

    product = mommy.make_recipe("products.product")
    cart = mommy.make_recipe("carts.cart", user=buyer)

    cart_item_1 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product,
        latest_delivery_date=date_2,
    )
    cart_item_2 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product,
        latest_delivery_date=date_1,
    )

    response = client_buyer.delete(f"/cart/{product.id}")

    assert response.status_code == 204

    assert Item.objects.get(latest_delivery_date=date_1).quantity == 1
    assert Item.objects.get(latest_delivery_date=date_2).quantity == 2

    with pytest.raises(CartItem.DoesNotExist):
        cart_item_1.refresh_from_db()

    with pytest.raises(CartItem.DoesNotExist):
        cart_item_2.refresh_from_db()
