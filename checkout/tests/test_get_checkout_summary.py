import pytest
from model_bakery import baker

from carts.models import CartItem
from delivery_options.models import DeliveryOption

pytestmark = pytest.mark.django_db


def test_get_the_latest_cart(seller, buyer, client_seller):
    cart_1 = baker.make("carts.Cart", user=seller)
    baker.make("carts.Cart", user=buyer)

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
        "grossTotal": 0.0,
        "vatBreakdown": {},
        "productTotal": 0,
        "deposit": [],
        "vatTotal": 0.0,
    }


def test_try_to_get_the_latest_cart(seller, client_seller):
    response = client_seller.get("/checkout")
    assert response.json() == {
        "earliestDeliveryDate": None,
        "deliveryAddress": None,
        "items": [],
    }


def test_get_checkout_with_delivery_address(buyer, client_buyer, delivery_address):
    baker.make("carts.Cart", user=buyer, delivery_address=delivery_address)
    response = client_buyer.get("/checkout")
    assert response.json()["deliveryAddress"] == delivery_address.id


def test_get_delivery_options(client_buyer, cart):
    response = client_buyer.get("/checkout")

    assert response.status_code == 200

    parsed_response = response.json()

    items = parsed_response["items"]

    cart_item_0 = CartItem.objects.get(id=items[0]["id"])
    cart_item_1 = CartItem.objects.get(id=items[1]["id"])

    assert cart_item_0.delivery_fee_gross == 21.42
    assert cart_item_0.delivery_fee_net == 18
    assert cart_item_0._delivery_fee().netto == cart_item_0.delivery_fee_net
    assert cart_item_1.delivery_fee_gross == 7.14
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
        parsed_response["deliveryFeeGross"]
        == cart_item_0.delivery_fee_gross + cart_item_1.delivery_fee_gross
    )
    assert (
        parsed_response["deliveryFeeNet"]
        == cart_item_0.delivery_fee_net + cart_item_1.delivery_fee_net
    )


def test_get_delivery_options_central_logistics_disabled(
    client_buyer, cart, traidoo_settings
):
    traidoo_settings.central_logistics_company = False
    traidoo_settings.save()

    assert not traidoo_settings.central_logistics_company

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


def test_get_deposit(client_buyer, cart):
    response = client_buyer.get("/checkout")

    assert response.status_code == 200

    parsed_response = response.json()

    item_1 = cart.items.all()[0]
    item_2 = cart.items.all()[1]

    assert parsed_response["deposit"] == [
        {
            "count": item_1.quantity,
            "depositNet": item_1.container_deposit.netto,
            "depositTotal": item_1.container_deposit.netto * item_1.quantity,
            "sizeClass": item_1.product.container_type.size_class,
            "unit": item_1.product.unit,
            "vat": float(item_1.product.vat),
            "volume": item_1.product.container_type.volume,
        },
        {
            "count": item_2.quantity,
            "depositNet": item_2.container_deposit.netto,
            "depositTotal": item_2.container_deposit.netto * item_1.quantity,
            "sizeClass": item_2.product.container_type.size_class,
            "unit": item_2.product.unit,
            "vat": float(item_2.product.vat),
            "volume": item_2.product.container_type.volume,
        },
    ]
