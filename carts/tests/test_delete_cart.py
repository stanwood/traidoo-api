import datetime

import pytest
from model_bakery import baker

from carts.models import CartItem
from items.models import Item


@pytest.mark.django_db
def test_delete_cart(buyer, client_buyer, traidoo_region):
    product_item = baker.make_recipe("items.item", quantity=9)
    cart = baker.make_recipe("carts.cart", user=buyer)
    cart_item = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item.product,
        latest_delivery_date=product_item.latest_delivery_date,
    )

    response = client_buyer.delete("/cart")

    assert response.status_code == 204

    product_item.refresh_from_db()
    assert product_item.quantity == 10

    with pytest.raises(CartItem.DoesNotExist):
        cart_item.refresh_from_db()
