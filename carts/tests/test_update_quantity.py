import datetime

import pytest
from model_mommy import mommy

from carts.models import CartItem
from items.models import Item


@pytest.mark.django_db
def test_increase_product_quantity(buyer, client_buyer, traidoo_region):
    product_item = mommy.make_recipe("items.item", quantity=10)
    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item.product,
        latest_delivery_date=product_item.latest_delivery_date,
    )

    response = client_buyer.post(
        "/cart", {"productId": product_item.product.id, "quantity": 2}
    )

    assert response.status_code == 200
    assert response.json() == {"notAvailable": 0}

    product_item.refresh_from_db()
    assert product_item.quantity == 9
    cart_item.refresh_from_db()
    assert cart_item.quantity == 2


@pytest.mark.django_db
def test_increase_product_quantity_from_multiple_product_items(
    buyer, client_buyer, traidoo_region
):
    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(days=2)
    date_3 = datetime.datetime.now() + datetime.timedelta(days=3)

    product_item_1 = mommy.make_recipe(
        "items.item", quantity=1, latest_delivery_date=date_1
    )
    product_item_2 = mommy.make_recipe(
        "items.item",
        product=product_item_1.product,
        quantity=2,
        latest_delivery_date=date_3,
    )
    product_item_3 = mommy.make_recipe(
        "items.item",
        product=product_item_1.product,
        quantity=3,
        latest_delivery_date=date_2,
    )

    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=1,
        product=product_item_1.product,
        latest_delivery_date=product_item_1.latest_delivery_date,
    )

    response = client_buyer.post(
        "/cart", {"productId": product_item_1.product.id, "quantity": 6}
    )

    assert response.status_code == 200
    assert response.json() == {"notAvailable": 0}

    product_item_1.refresh_from_db()
    assert product_item_1.quantity == 0
    product_item_3.refresh_from_db()
    assert product_item_3.quantity == 0
    product_item_2.refresh_from_db()
    assert product_item_2.quantity == 1

    cart_item.refresh_from_db()
    assert cart_item.quantity == 2

    assert (
        CartItem.objects.get(
            product=product_item_1.product, latest_delivery_date=date_1
        ).quantity
        == 2
    )
    assert (
        CartItem.objects.get(
            product=product_item_2.product, latest_delivery_date=date_3
        ).quantity
        == 1
    )
    assert (
        CartItem.objects.get(
            product=product_item_3.product, latest_delivery_date=date_2
        ).quantity
        == 3
    )


@pytest.mark.django_db
def test_decrease_product_quantity(buyer, client_buyer, traidoo_region):
    product_item = mommy.make_recipe("items.item", quantity=10)
    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product_item.product,
        latest_delivery_date=product_item.latest_delivery_date,
    )

    response = client_buyer.post(
        "/cart", {"productId": product_item.product.id, "quantity": 1}
    )

    assert response.status_code == 204

    product_item.refresh_from_db()
    assert product_item.quantity == 11
    cart_item.refresh_from_db()
    assert cart_item.quantity == 1


@pytest.mark.django_db
def test_decrease_product_quantity_from_multiple_product_items(
    buyer, client_buyer, traidoo_region
):
    date_1 = datetime.datetime.now() + datetime.timedelta(days=1)
    date_2 = datetime.datetime.now() + datetime.timedelta(days=2)
    date_3 = datetime.datetime.now() + datetime.timedelta(days=3)

    product_item_1 = mommy.make_recipe(
        "items.item", quantity=1, latest_delivery_date=date_1
    )
    product_item_2 = mommy.make_recipe(
        "items.item",
        product=product_item_1.product,
        quantity=2,
        latest_delivery_date=date_2,
    )

    cart = mommy.make_recipe("carts.cart", user=buyer)
    cart_item_1 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product_item_1.product,
        latest_delivery_date=product_item_1.latest_delivery_date,
    )
    cart_item_2 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product_item_2.product,
        latest_delivery_date=product_item_2.latest_delivery_date,
    )
    cart_item_3 = mommy.make_recipe(
        "carts.cartitem",
        cart=cart,
        quantity=2,
        product=product_item_2.product,
        latest_delivery_date=date_3,
    )

    response = client_buyer.post(
        "/cart", {"productId": product_item_1.product.id, "quantity": 1}
    )
    assert response.status_code == 204

    with pytest.raises(CartItem.DoesNotExist):
        cart_item_3.refresh_from_db()

    with pytest.raises(CartItem.DoesNotExist):
        cart_item_2.refresh_from_db()

    cart_item_1.refresh_from_db()
    assert cart_item_1.quantity == 1

    product_item_1.refresh_from_db()
    assert product_item_1.quantity == 2

    product_item_2.refresh_from_db()
    assert product_item_2.quantity == 4

    assert (
        Item.objects.get(
            product=product_item_1.product, latest_delivery_date=date_3
        ).quantity
        == 2
    )
