import datetime

import pytest
from django.utils import timezone
from model_bakery import baker


@pytest.mark.django_db
def test_get_cart(buyer, client_buyer):
    delivery_address = baker.make_recipe(
        "delivery_addresses.delivery_address", user=buyer
    )

    product_item_1 = baker.make_recipe(
        "items.item",
        quantity=9,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=1),
    )
    product_item_2 = baker.make_recipe(
        "items.item",
        product=product_item_1.product,
        quantity=4,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=2),
    )

    product_item_3 = baker.make(
        "items.item",
        quantity=10,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
    )

    cart = baker.make_recipe(
        "carts.cart", user=buyer, delivery_address=delivery_address
    )

    cart_item_1 = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item_1.product,
        latest_delivery_date=product_item_1.latest_delivery_date,
    )
    cart_item_2 = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product_item_2.product,
        latest_delivery_date=product_item_2.latest_delivery_date,
    )
    cart_item_3 = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=4,
        product=product_item_3.product,
        latest_delivery_date=product_item_3.latest_delivery_date,
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
            },
            {
                "id": product_item_3.product.id,
                "amount": float(product_item_3.product.amount),
                "name": product_item_3.product.name,
                "price": float(product_item_3.product.price),
                "unit": product_item_3.product.unit,
                "quantity": cart_item_3.quantity,
            },
        ],
    }
