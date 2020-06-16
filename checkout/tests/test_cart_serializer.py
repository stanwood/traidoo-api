from decimal import Decimal
from unittest import mock

from model_mommy import mommy

from checkout.serializers import CartSerializer
from delivery_options.models import DeliveryOption


def test_seller_delivery_fee_calculation(client_buyer, buyer, settings):
    settings.FEATURES["routes"] = True
    product = mommy.make_recipe("products.product", third_party_delivery=True)
    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
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
