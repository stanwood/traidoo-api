import datetime

import pytest
from django.utils import timezone
from model_mommy import mommy


@pytest.mark.django_db
def test_get_cart(buyer, client_buyer, traidoo_region):
    delivery_address = mommy.make_recipe(
        "delivery_addresses.delivery_address", user=buyer
    )

    product_item_1 = mommy.make_recipe(
        "items.item",
        quantity=9,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=1),
    )
    product_item_2 = mommy.make_recipe(
        "items.item",
        product=product_item_1.product,
        quantity=4,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=2),
    )

    cart = mommy.make_recipe(
        "carts.cart", user=buyer, delivery_address=delivery_address
    )

    cart_item_1 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item_1.product,
        latest_delivery_date=product_item_1.latest_delivery_date,
    )
    cart_item_2 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product_item_2.product,
        latest_delivery_date=product_item_2.latest_delivery_date,
    )

    response = client_buyer.get("/cart")

    assert response.json() == {
        "products": [
            {
                "id": product_item_1.product.id,
                "amount": float(product_item_1.product.amount),
                "name": product_item_1.product.name,
                "price": float(product_item_1.product.price),
                "unit": product_item_1.product.unit,
                "quantity": cart_item_1.quantity + cart_item_2.quantity,
            }
        ],
    }
