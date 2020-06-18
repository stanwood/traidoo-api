import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_cart_item_delivery_option(buyer, client_buyer, traidoo_region):
    cart = baker.make_recipe("carts.cart", user=buyer)
    cart_item = baker.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, delivery_option_id=0
    )

    assert cart_item.delivery_option.id == 0

    response = client_buyer.post(
        f"/cart/{cart_item.product.id}/delivery_option", {"delivery_option": 1}
    )

    assert response.status_code == 204

    cart_item.refresh_from_db()
    assert cart_item.delivery_option.id == 1
