import pytest
from model_mommy import mommy

from carts.models import CartItem
from delivery_options.models import DeliveryOption

pytestmark = pytest.mark.django_db


def test_get_the_latest_cart(seller, buyer, client_seller):
    cart_1 = mommy.make("carts.Cart", user=seller)
    mommy.make("carts.Cart", user=buyer)

    response = client_seller.get("/checkout")
    assert response.json() == {
        "id": cart_1.id,
        "items": [],
        "earliestDeliveryDate": None,
        "deliveryAddress": None,
        "totalContainerDeposit": 0.0,
        "platformFeeNet": 0,
        "platformFeeGross": 0,
        "deliveryFeeNet": 0,
        "deliveryFeeGross": 0,
        "netTotal": 0.0,
        "vatBreakdown": {"19.0": 0.0},
        "productTotal": 0,
        "deposit": [],
        "vatTotal": 0.0,
    }


def test_try_to_get_the_latest_cart(seller, client_seller):
    response = client_seller.get("/checkout")
    assert response.json() == {
        "earliestDeliveryDate": None,
        "deliveryAddress": None,
        "user": None,
        "items": [],
    }


def test_get_cart_with_delivery_address(buyer, client_buyer, delivery_address):
    cart = mommy.make("carts.Cart", user=buyer, delivery_address=delivery_address)
    response = client_buyer.get("/checkout")
    assert response.json()["deliveryAddress"] == delivery_address.id


def test_get_delivery_options(client_buyer, cart):
    response = client_buyer.get("/checkout")

    assert response.status_code == 200

    parsed_response = response.json()

    items = parsed_response["items"]

    cart_item_0 = CartItem.objects.get(id=items[0]["id"])
    cart_item_1 = CartItem.objects.get(id=items[1]["id"])

    assert cart_item_0.delivery_fee_gross == 32.73
    assert cart_item_0.delivery_fee_net == 27.5
    assert cart_item_0._delivery_fee().netto == cart_item_0.delivery_fee_net
    assert cart_item_1.delivery_fee_gross == 11.31
    assert cart_item_1.delivery_fee_net == 9.5
    assert cart_item_1._delivery_fee().netto == cart_item_1.delivery_fee_net

    assert items[0]["deliveryOptions"] == [
        {"id": DeliveryOption.SELLER, "value": 1.1},
        {"id": DeliveryOption.BUYER, "value": 0.0},
        {"id": DeliveryOption.CENTRAL_LOGISTICS, "value": cart_item_0.delivery_fee_net},
    ]
    assert items[1]["deliveryOptions"] == [
        {"id": DeliveryOption.SELLER, "value": 1.1},
        {"id": DeliveryOption.BUYER, "value": 0.0},
        {"id": DeliveryOption.CENTRAL_LOGISTICS, "value": cart_item_1.delivery_fee_net},
    ]

    assert (
        parsed_response["deliveryFeeGross"]
        == cart_item_0.delivery_fee_gross + cart_item_1.delivery_fee_gross
    )
    assert (
        parsed_response["deliveryFeeNet"]
        == cart_item_0.delivery_fee_net + cart_item_1.delivery_fee_net
    )


def test_get_delivery_options_central_logistics_disabled(
    client_buyer, cart, mcs_settings
):
    mcs_settings.central_logistics_company = False
    mcs_settings.save()

    assert not mcs_settings.central_logistics_company

    response = client_buyer.get("/checkout")

    assert response.status_code == 200

    parsed_response = response.json()

    items = parsed_response["items"]
    assert items[0]["deliveryOptions"] == [
        {"id": DeliveryOption.SELLER, "value": 1.1},
        {"id": DeliveryOption.BUYER, "value": 0.0},
    ]
    assert items[1]["deliveryOptions"] == [
        {"id": DeliveryOption.SELLER, "value": 1.1},
        {"id": DeliveryOption.BUYER, "value": 0.0},
    ]
