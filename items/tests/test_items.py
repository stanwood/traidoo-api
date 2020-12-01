import datetime

import pytest
from django.utils import timezone
from model_bakery import baker
from items.models import Item


YMD_FORMAT = "%Y-%m-%d"


@pytest.mark.django_db
def test_get_product_items(client_seller, seller):
    product = baker.make_recipe("products.product", seller=seller)
    item = baker.make_recipe("items.item", product=product)

    response = client_seller.get(
        f"/items/{product.id}",
    )

    assert response.json() == [
        {
            "id": item.id,
            "product": item.product.id,
            "createdAt": item.created_at.isoformat().replace("+00:00", "Z"),
            "updatedAt": item.updated_at.isoformat().replace("+00:00", "Z"),
            "latestDeliveryDate": item.latest_delivery_date.strftime("%Y-%m-%d"),
            "quantity": item.quantity,
            "validFrom": None,
        }
    ]


@pytest.mark.django_db
def test_add_product_item(client_seller, seller):
    product = baker.make_recipe("products.product", seller=seller)

    quantity = 222
    delivery_date = timezone.now().date() + datetime.timedelta(days=1)

    assert Item.objects.count() == 0

    response = client_seller.post(
        f"/items/{product.id}",
        {
            "latestDeliveryDate": delivery_date.strftime(YMD_FORMAT),
            "quantity": quantity,
        },
    )

    assert response.status_code == 204

    item = Item.objects.get()
    assert item.product.id == product.id
    assert item.latest_delivery_date == delivery_date
    assert item.quantity == quantity


@pytest.mark.django_db
def test_add_product_item_with_the_same_delivery_date(client_seller, seller):
    delivery_date = timezone.now().date() + datetime.timedelta(days=1)
    product = baker.make_recipe("products.product", seller=seller)
    baker.make_recipe("items.item", product=product, latest_delivery_date=delivery_date)

    assert Item.objects.count() == 1

    response = client_seller.post(
        f"/items/{product.id}",
        {"latestDeliveryDate": delivery_date.strftime(YMD_FORMAT), "quantity": 123},
    )

    assert response.status_code == 400
    assert response.json() == {
        "nonFieldErrors": [
            {
                "message": "The fields product, latest_delivery_date must make a unique set.",
                "code": "unique",
            }
        ]
    }

    assert Item.objects.count() == 1


@pytest.mark.django_db
def test_update_product_item(client_seller, seller):
    delivery_date_1 = timezone.now().date() + datetime.timedelta(days=1)
    delivery_date_2 = timezone.now().date() + datetime.timedelta(days=1)
    quantity_1 = 111
    quantity_2 = 222

    product = baker.make_recipe("products.product", seller=seller)
    item = baker.make_recipe(
        "items.item",
        product=product,
        latest_delivery_date=delivery_date_1,
        quantity=quantity_1,
    )

    assert Item.objects.count() == 1

    response = client_seller.patch(
        f"/items/{product.id}/{item.id}",
        {
            "latestDeliveryDate": delivery_date_2.strftime(YMD_FORMAT),
            "quantity": quantity_2,
        },
    )

    assert response.status_code == 204

    assert Item.objects.count() == 1

    item.refresh_from_db()
    assert item.product == product
    assert item.latest_delivery_date == delivery_date_2
    assert item.quantity == quantity_2


@pytest.mark.django_db
def test_update_product_item_does_not_exist(client_seller, seller):
    delivery_date = timezone.now().date() + datetime.timedelta(days=1)

    response = client_seller.patch(
        f"/items/123/234",
        {"latestDeliveryDate": delivery_date.strftime(YMD_FORMAT), "quantity": 1},
    )

    assert response.status_code == 404
