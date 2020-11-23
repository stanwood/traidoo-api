import pytest

from carts.models import CartItem
from delivery_options.models import DeliveryOption

pytestmark = pytest.mark.django_db


def test_get_checkout_delivery_options(client_buyer, cart):
    response = client_buyer.get("/checkout/delivery")

    assert response.status_code == 200

    parsed_response = response.json()

    items = parsed_response["items"]

    cart_item_0 = CartItem.objects.get(id=items[0]["id"])
    cart_item_1 = CartItem.objects.get(id=items[1]["id"])

    assert cart_item_0.delivery_fee_net == 18
    assert cart_item_0._delivery_fee().netto == cart_item_0.delivery_fee_net
    assert cart_item_1.delivery_fee_net == 6.0
    assert cart_item_1._delivery_fee().netto == cart_item_1.delivery_fee_net

    assert {"id": DeliveryOption.SELLER, "value": 1.1} in items[0]["deliveryOptions"]
    assert {"id": DeliveryOption.BUYER, "value": 0.0} in items[0]["deliveryOptions"]
    assert {
        "id": DeliveryOption.CENTRAL_LOGISTICS,
        "value": cart_item_0.delivery_fee_net,
    } in items[0]["deliveryOptions"]

    assert {"id": DeliveryOption.SELLER, "value": 1.1} in items[1]["deliveryOptions"]
    assert {"id": DeliveryOption.BUYER, "value": 0.0} in items[1]["deliveryOptions"]
    assert {
        "id": DeliveryOption.CENTRAL_LOGISTICS,
        "value": cart_item_1.delivery_fee_net,
    } in items[1]["deliveryOptions"]

    assert (
        parsed_response["deliveryFeeNet"]
        == cart_item_0.delivery_fee_net + cart_item_1.delivery_fee_net
    )
