import datetime
import time
from unittest import mock

import pytest
from django.utils import timezone
from model_bakery import baker

from carts.models import Cart, CartItem
from orders.models import OrderItem

pytestmark = pytest.mark.django_db


def test_run_job_task_feature_disabled(
    buyer,
    client_buyer,
    products,
    delivery_address,
    delivery_options,
    send_task,
    logistics_user,
    platform_user,
    settings,
):
    settings.FEATURES = {"routes": False}

    products[0].third_party_delivery = True
    products[0].save()
    products[1].third_party_delivery = True
    products[1].save()

    cart = baker.make(
        Cart,
        user=buyer,
        delivery_address=delivery_address,
        earliest_delivery_date=(
            datetime.datetime.now() + datetime.timedelta(days=2)
        ).date(),
    )

    baker.make(
        CartItem,
        product=products[0],
        cart=cart,
        quantity=1,
        delivery_option=delivery_options[0],
    )
    baker.make(
        CartItem,
        product=products[1],
        cart=cart,
        quantity=2,
        delivery_option=delivery_options[0],
    )

    assert not OrderItem.objects.first()

    response = client_buyer.post("/checkout")
    assert response.status_code == 200

    assert not [task for task in send_task.call_args_list if "jobs" in task[0][0]]


def test_job_task_third_party_delivery(
    buyer,
    client_buyer,
    products,
    delivery_address,
    delivery_options,
    send_task,
    logistics_user,
    platform_user,
    settings,
    traidoo_region,
):
    settings.FEATURES = {"routes": True}

    products[0].third_party_delivery = False
    products[0].save()
    products[1].third_party_delivery = True
    products[1].save()

    cart = baker.make(
        Cart,
        user=buyer,
        delivery_address=delivery_address,
        earliest_delivery_date=(
            datetime.datetime.now() + datetime.timedelta(days=2)
        ).date(),
    )
    baker.make(
        CartItem,
        product=products[0],
        cart=cart,
        quantity=1,
        delivery_option=delivery_options[1],
    )

    baker.make(
        CartItem,
        product=products[1],
        cart=cart,
        quantity=2,
        delivery_option=delivery_options[1],
    )

    assert not OrderItem.objects.first()

    response = client_buyer.post("/checkout")
    assert response.status_code == 200

    assert OrderItem.objects.count() == 2
    order_item_1 = OrderItem.objects.filter(product__third_party_delivery=True).first()
    order_item_2 = OrderItem.objects.filter(product__third_party_delivery=False).first()
    assert order_item_1.id != order_item_2.id

    assert (
        mock.call(
            f"/jobs/create/{order_item_1.order.id}",
            http_method="POST",
            queue_name="routes",
            schedule_time=30,
            headers={"Region": traidoo_region.slug},
        )
        in send_task.call_args_list
    )
    assert (
        mock.call(
            f"/jobs/create/{order_item_2.order.id}",
            http_method="POST",
            queue_name="routes",
            schedule_time=30,
            headers={"Region": traidoo_region.slug},
        )
        in send_task.call_args_list
    )


def test_job_task_seller_delivery(
    buyer,
    client_buyer,
    products,
    delivery_address,
    delivery_options,
    send_task,
    logistics_user,
    platform_user,
    settings,
    traidoo_region,
):
    settings.FEATURES = {"routes": True}

    products[0].third_party_delivery = True
    products[0].save()
    products[1].third_party_delivery = True
    products[1].save()

    cart = baker.make(
        Cart,
        user=buyer,
        delivery_address=delivery_address,
        earliest_delivery_date=(
            datetime.datetime.now() + datetime.timedelta(days=2)
        ).date(),
    )
    baker.make(
        CartItem,
        product=products[0],
        cart=cart,
        quantity=1,
        delivery_option=delivery_options[0],
    )

    baker.make(
        CartItem,
        product=products[1],
        cart=cart,
        quantity=2,
        delivery_option=delivery_options[1],
    )

    assert not OrderItem.objects.first()

    response = client_buyer.post("/checkout")
    assert response.status_code == 200

    assert OrderItem.objects.count() == 2
    order_item_1 = OrderItem.objects.filter(delivery_option=delivery_options[1]).first()
    order_item_2 = OrderItem.objects.filter(delivery_option=delivery_options[0]).first()
    assert order_item_1.id != order_item_2.id

    assert (
        mock.call(
            f"/jobs/create/{order_item_1.order.id}",
            http_method="POST",
            queue_name="routes",
            schedule_time=30,
            headers={"Region": traidoo_region.slug},
        )
        in send_task.call_args_list
    )
    assert (
        mock.call(
            f"/jobs/create/{order_item_2.order.id}",
            http_method="POST",
            queue_name="routes",
            schedule_time=30,
            headers={"Region": traidoo_region.slug},
        )
        in send_task.call_args_list
    )
