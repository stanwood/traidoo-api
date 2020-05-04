import datetime

import pytest
from model_mommy import mommy


@pytest.mark.django_db
def test_get_cart(buyer, client_buyer, traidoo_region):
    product_item = mommy.make_recipe("items.item", quantity=9)
    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item.product,
        latest_delivery_date=product_item.latest_delivery_date,
    )

    response = client_buyer.get("/cart")

    assert response.json() == {
        "earliestDeliveryDate": cart.earliest_delivery_date,
        "items": {
            f"{product_item.product.id}": {
                "product": {
                    "amount": float(product_item.product.amount),
                    "name": product_item.product.name,
                    "price": float(product_item.product.price),
                    "unit": product_item.product.unit,
                },
                "quantity": cart_item.quantity,
            }
        },
    }
