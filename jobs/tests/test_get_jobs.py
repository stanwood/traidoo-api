import datetime

import pytest
from dictdiffer import diff
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_mommy import mommy

from delivery_addresses.models import DeliveryAddress
from orders.models import Order, OrderItem
from products.models import Product
from routes.models import Route

from ..models import Detour, Job

User = get_user_model()


pytestmark = pytest.mark.django_db


def _generate_job_response_dict(
    job, detour, delivery_address, order, order_item, product, user=None
):
    return {
        "createdAt": job.created_at.isoformat().replace("+00:00", "Z"),
        "detour": detour.length,
        "id": job.id,
        "orderItem": {
            "deliveryAddress": {
                "city": delivery_address.city,
                "companyName": delivery_address.company_name,
                "street": delivery_address.street,
                "zip": delivery_address.zip,
            },
            "deliveryDate": order_item.delivery_date.strftime("%Y-%m-%d"),
            "deliveryFee": order_item.delivery_fee,
            "latestDeliveryDate": order_item.latest_delivery_date.strftime("%Y-%m-%d"),
            "order": {
                "earliestDeliveryDate": order.earliest_delivery_date.isoformat().replace(
                    "+00:00", "Z"
                )
            },
            "product": {
                "amount": float(product.amount),
                "containerType": {"sizeClass": product.container_type.size_class},
                "name": product.name,
                "seller": {
                    "city": product.seller.city,
                    "companyName": product.seller.company_name,
                    "firstName": product.seller.first_name,
                    "lastName": product.seller.last_name,
                    "street": product.seller.street,
                    "zip": product.seller.zip,
                },
                "unit": product.unit,
            },
            "quantity": order_item.quantity,
        },
        "updatedAt": job.updated_at.isoformat().replace("+00:00", "Z"),
        "user": user.id if user else None,
    }


def _create_test_data():
    user_1 = mommy.make_recipe("users.user")
    user_2 = mommy.make_recipe("users.user")

    route_1 = mommy.make_recipe("routes.route", user=user_1)
    route_2 = mommy.make_recipe("routes.route", user=user_1)

    delivery_address_1 = mommy.make_recipe("delivery_addresses.delivery_address")
    delivery_address_2 = mommy.make_recipe("delivery_addresses.delivery_address")

    product_1 = mommy.make_recipe("products.product", seller=user_2)
    product_2 = mommy.make_recipe("products.product", seller=user_2)
    product_3 = mommy.make_recipe("products.product", seller=user_2)

    order = mommy.make(
        Order,
        earliest_delivery_date=timezone.make_aware(
            datetime.datetime.now() + datetime.timedelta(days=1)
        ),
    )
    order_item_1 = mommy.make(
        OrderItem,
        delivery_address=delivery_address_1,
        product=product_1,
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=6),
        order=order,
    )
    order_item_2 = mommy.make(
        OrderItem,
        delivery_address=delivery_address_2,
        product=product_2,
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=2),
        order=order,
    )
    order_item_3 = mommy.make(
        OrderItem,
        delivery_address=delivery_address_2,
        product=product_2,
        latest_delivery_date=datetime.date.today() + datetime.timedelta(hours=23),
        order=order,
    )
    order_item_4 = mommy.make(
        OrderItem,
        delivery_address=delivery_address_2,
        product=product_3,
        latest_delivery_date=datetime.datetime.today() + datetime.timedelta(days=6),
        order=order,
    )

    job_1 = mommy.make(Job, order_item=order_item_1, user=None)
    job_2 = mommy.make(Job, order_item=order_item_2, user=None)
    job_3 = mommy.make(Job, order_item=order_item_3, user=None)
    job_4 = mommy.make(Job, order_item=order_item_4, user=user_1)

    detour_1 = mommy.make(Detour, job=job_1, route=route_1, length=100)
    detour_2 = mommy.make(Detour, job=job_1, route=route_2, length=200)
    detour_3 = mommy.make(Detour, job=job_2, route=route_1, length=300)
    detour_4 = mommy.make(Detour, job=job_2, route=route_2, length=250)
    detour_5 = mommy.make(Detour, job=job_3, route=route_2, length=111)
    detour_6 = mommy.make(Detour, job=job_4, route=route_2, length=111)

    return (
        (user_1, user_2),
        (route_1, route_2),
        (delivery_address_1, delivery_address_2),
        (product_1, product_2, product_3),
        (order,),
        (order_item_1, order_item_2, order_item_3, order_item_4),
        (job_1, job_2, job_3, job_4),
        (detour_1, detour_2, detour_3, detour_4, detour_5, detour_6),
    )


def test_get_jobs(api_client, settings, django_assert_num_queries):
    settings.FEATURES["routes"] = True

    (
        users,
        _,
        delivery_addresses,
        products,
        orders,
        order_items,
        jobs,
        detours,
    ) = _create_test_data()

    api_client.force_authenticate(user=users[0])

    with django_assert_num_queries(5):
        response = api_client.get("/jobs")

    json_response = response.json()

    assert json_response["count"] == 2

    expected_response_1 = _generate_job_response_dict(
        jobs[1],
        detours[3],
        delivery_addresses[1],
        orders[0],
        order_items[1],
        products[1],
    )
    expected_response_2 = _generate_job_response_dict(
        jobs[0],
        detours[0],
        delivery_addresses[0],
        orders[0],
        order_items[0],
        products[0],
    )

    assert not list(diff(json_response["results"][0], expected_response_1))
    assert not list(diff(json_response["results"][1], expected_response_2))


def test_do_not_show_jobs_when_order_was_processed(
    api_client, settings, django_assert_num_queries
):
    settings.FEATURES["routes"] = True

    (
        users,
        _,
        delivery_addresses,
        products,
        orders,
        order_items,
        jobs,
        detours,
    ) = _create_test_data()

    orders[0].processed = True
    orders[0].save()

    api_client.force_authenticate(user=users[0])

    with django_assert_num_queries(4):
        response = api_client.get("/jobs")

    json_response = response.json()

    assert json_response["count"] == 0


def test_get_own_jobs(api_client, settings, django_assert_num_queries):
    settings.FEATURES["routes"] = True

    (
        users,
        _,
        delivery_addresses,
        products,
        orders,
        order_items,
        jobs,
        detours,
    ) = _create_test_data()

    api_client.force_authenticate(user=users[0])

    with django_assert_num_queries(5):
        response = api_client.get("/jobs?my=true")

    json_response = response.json()

    assert json_response["count"] == 1

    expected_response_1 = _generate_job_response_dict(
        jobs[3],
        detours[5],
        delivery_addresses[0],
        orders[0],
        order_items[3],
        products[2],
        users[0],
    )

    assert not list(diff(json_response["results"][0], expected_response_1))


def test_order_jobs_by_delivery_fee(
    client_seller, seller, settings, django_assert_num_queries
):
    settings.FEATURES["routes"] = True

    route_1 = mommy.make_recipe("routes.route", user=seller)
    route_2 = mommy.make_recipe("routes.route", user=seller)

    order_item_1 = mommy.make_recipe(
        "orders.orderitem",
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=6),
    )
    order_item_2 = mommy.make_recipe(
        "orders.orderitem",
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=6),
    )

    job_1 = mommy.make(Job, order_item=order_item_1, user=None)
    job_2 = mommy.make(Job, order_item=order_item_2, user=None)

    detour_1 = mommy.make(Detour, job=job_1, route=route_1, length=100)
    detour_2 = mommy.make(Detour, job=job_2, route=route_2, length=200)

    with django_assert_num_queries(5):
        response_json = client_seller.get(
            "/jobs?offset=0&ordering=order_item__delivery_fee&limit=15"
        ).json()

    assert response_json["count"] == 2
    assert response_json["results"][0]["id"] == job_1.id
    assert response_json["results"][1]["id"] == job_2.id
