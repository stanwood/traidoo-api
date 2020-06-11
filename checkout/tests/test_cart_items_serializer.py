from unittest import mock

from model_mommy import mommy

from checkout.serializers import CartItemSerializer


def test_cart_item_delivery_options(db, buyer):
    seller_delivery_option = mommy.make_recipe("delivery_options.seller")
    product = mommy.make_recipe(
        "products.product", delivery_options=[seller_delivery_option]
    )
    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
        "carts.cartitem", cart=cart, quantity=1, product=product
    )

    fake_request = mock.MagicMock(headers={"Region": cart_item.product.region.slug})
    serializer = CartItemSerializer(
        instance=cart_item, context={"request": fake_request}
    )

    cart_delivery_options_ids = {
        option["id"] for option in serializer.get_delivery_options(cart_item)
    }

    product_delivery_options_ids = {
        option.id for option in cart_item.product.delivery_options.all()
    }

    assert cart_delivery_options_ids == product_delivery_options_ids