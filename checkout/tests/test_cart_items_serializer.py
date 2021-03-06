from unittest import mock

from model_bakery import baker

from checkout.serializers.checkout import CartItemSerializer


def test_cart_item_delivery_options(db, buyer):
    seller_delivery_option = baker.make_recipe("delivery_options.seller")
    product = baker.make_recipe(
        "products.product", delivery_options=[seller_delivery_option]
    )
    cart = baker.make_recipe("carts.cart", user=buyer)
    cart_item = baker.make_recipe(
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


def test_include_price_net(db, buyer):
    product = baker.make_recipe("products.product", price=10, amount=2)
    region = baker.make_recipe("common.region")
    cart = baker.make_recipe("carts.cart", user=buyer)
    cart.user.region = region
    cart.user.save()
    cart_item = baker.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product,
        delivery_option=product.delivery_options.first(),
    )

    fake_request = mock.MagicMock(headers={"Region": cart_item.product.region.slug})
    serializer = CartItemSerializer(
        instance=cart_item, context={"request": fake_request}
    )

    assert serializer.data["price_net"] == product.price * product.amount
