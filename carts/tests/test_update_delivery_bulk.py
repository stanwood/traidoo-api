import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_cart_delivery_option_bulk_update(
    buyer, client_buyer, traidoo_region, delivery_options
):
    product_1 = baker.make_recipe("products.product", delivery_options=delivery_options)
    product_2 = baker.make_recipe(
        "products.product", delivery_options=[delivery_options[0]]
    )
    product_3 = baker.make_recipe(
        "products.product", delivery_options=[delivery_options[1], delivery_options[2]]
    )
    product_4 = baker.make_recipe(
        "products.product", delivery_options=[delivery_options[2]]
    )
    product_5 = baker.make_recipe(
        "products.product", delivery_options=[delivery_options[1]]
    )

    cart = baker.make_recipe("carts.cart", user=buyer)

    cart_item_1 = baker.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, product=product_1
    )
    cart_item_2 = baker.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, product=product_2
    )
    cart_item_3 = baker.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, product=product_3
    )
    cart_item_4 = baker.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, product=product_4
    )
    cart_item_5 = baker.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, product=product_5
    )

    assert not cart_item_1.delivery_option
    assert not cart_item_2.delivery_option
    assert not cart_item_3.delivery_option
    assert not cart_item_4.delivery_option
    assert not cart_item_5.delivery_option

    response = client_buyer.post(
        f"/cart/deliveryOption", {"delivery_option": delivery_options[1].id}
    )

    assert response.status_code == 204

    cart_item_1.refresh_from_db()
    cart_item_2.refresh_from_db()
    cart_item_3.refresh_from_db()
    cart_item_4.refresh_from_db()
    cart_item_5.refresh_from_db()

    assert cart_item_1.delivery_option.id == delivery_options[1].id
    assert not cart_item_2.delivery_option
    assert cart_item_3.delivery_option.id == delivery_options[1].id
    assert not cart_item_4.delivery_option
    assert cart_item_5.delivery_option.id == delivery_options[1].id
