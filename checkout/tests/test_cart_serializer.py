from decimal import Decimal
from unittest import mock

from model_bakery import baker

from checkout.serializers import CartSerializer
from delivery_options.models import DeliveryOption


def test_seller_delivery_fee_calculation(client_buyer, buyer, settings):
    settings.FEATURES["routes"] = True
    product = baker.make_recipe("products.product", third_party_delivery=True)
    cart = baker.make_recipe("carts.cart", user=buyer)
    cart_item = baker.make_recipe(
        "carts.cartitem",
        delivery_option_id=DeliveryOption.SELLER,
        quantity=1,
        cart=cart,
        product=product,
    )
    fake_request = mock.MagicMock(headers={"Region": cart_item.product.region.slug})
    serializer = CartSerializer(instance=cart, context={"request": fake_request})
    assert (
        Decimal(str(serializer.get_delivery_fee_net(cart)))
        == cart_item.product.delivery_charge
    )

    response = client_buyer.get("/checkout")
    assert (
        Decimal(str(response.data["delivery_fee_net"]))
        == cart_item.product.delivery_charge
    )


def test_vat_breakdown(buyer):
    container = baker.make_recipe("containers.container", deposit=4, delivery_fee=2)
    seller_delivery_option = baker.make_recipe("delivery_options.seller")
    logistics_delivery_option = baker.make_recipe("delivery_options.central_logistic")
    product_1 = baker.make_recipe(
        "products.product",
        price=9.17,
        amount=7,
        vat=10.7,
        delivery_charge=0.13,
        container_type=container,
        delivery_options=[seller_delivery_option, logistics_delivery_option],
    )
    product_2 = baker.make_recipe(
        "products.product",
        price=3.19,
        amount=10,
        vat=10.7,
        container_type=container,
        delivery_options=[seller_delivery_option, logistics_delivery_option],
    )

    cart = baker.make_recipe("carts.cart", user=buyer)
    cart_item = baker.make_recipe(
        "carts.cartitem",
        delivery_option=seller_delivery_option,
        quantity=1,
        cart=cart,
        product=product_1,
    )
    baker.make_recipe(
        "carts.cartitem",
        delivery_option=logistics_delivery_option,
        quantity=1,
        product=product_2,
        cart=cart,
    )

    fake_request = mock.MagicMock(headers={"Region": cart_item.product.region.slug})
    serializer = CartSerializer(instance=cart, context={"request": fake_request})
    breakdown, total = serializer._vat_breakdown(cart)
    assert breakdown[19.0] == 2.45
    assert breakdown[10.7] == 10.28
    assert total == 12.73
