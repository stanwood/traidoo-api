import datetime
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_bakery import baker

from delivery_addresses.models import DeliveryAddress
from orders.models import Order, OrderItem
from products.models import Product
from routes.models import Route

from ..models import Detour, Job

User = get_user_model()


pytestmark = pytest.mark.django_db


@mock.patch("jobs.tasks.create_job.calculate_route_length")
def test_create_job_task_order_not_found(
    calculate_route_length_mock, client_anonymous, settings
):
    settings.FEATURES["routes"] = True

    response = client_anonymous.post(
        f"/jobs/create/123123123", **{"HTTP_X_APPENGINE_QUEUENAME": "queue"}
    )

    assert response.status_code == 200
    assert not Job.objects.first()
    assert not Detour.objects.first()
    calculate_route_length_mock.assert_not_called()


@mock.patch("jobs.tasks.create_job.calculate_route_length")
def test_create_job_task_product_without_third_party_delivery(
    calculate_route_length_mock, client_anonymous, settings, traidoo_region
):
    settings.FEATURES["routes"] = True

    product = baker.make(Product, third_party_delivery=False, region=traidoo_region)
    order = baker.make(Order)
    baker.make_recipe("orders.orderitem", order=order, product=product)

    response = client_anonymous.post(
        f"/jobs/create/{order.id}", **{"HTTP_X_APPENGINE_QUEUENAME": "queue"}
    )

    assert response.status_code == 200

    assert not Job.objects.first()
    assert not Detour.objects.first()
    calculate_route_length_mock.assert_not_called()


@mock.patch("jobs.tasks.create_job.calculate_route_length")
def test_create_job_user_without_routes(
    calculate_route_length_mock, client_anonymous, settings, traidoo_region
):
    settings.FEATURES["routes"] = True

    product = baker.make(Product, third_party_delivery=False, region=traidoo_region)
    order = baker.make(Order)
    baker.make_recipe("orders.orderitem", order=order, product=product)
    baker.make(User, is_email_verified=True, is_active=True)

    response = client_anonymous.post(
        f"/jobs/create/{order.id}", **{"HTTP_X_APPENGINE_QUEUENAME": "queue"}
    )

    assert response.status_code == 200

    assert not Job.objects.first()
    assert not Detour.objects.first()
    calculate_route_length_mock.assert_not_called()


@mock.patch("jobs.tasks.create_job.calculate_route_length")
def test_create_job_for_order_item(
    calculate_route_length_mock, client_anonymous, settings, traidoo_region
):
    settings.FEATURES["routes"] = True

    default_route_length = 1200
    calculate_route_length_mock.return_value = default_route_length

    assert not Job.objects.first()
    assert not Detour.objects.first()

    buyer = baker.make(User, is_email_verified=True, is_active=True)
    seller_1 = baker.make(
        User,
        is_email_verified=True,
        is_active=True,
        company_name="Seller Company Name",
        zip="123",
        city="Seller City",
        street="Seller Street",
    )
    seller_2 = baker.make(
        User,
        is_email_verified=True,
        is_active=True,
        company_name="Seller Company Name",
        zip="123",
        city="Seller City",
        street="Seller Street",
    )

    route_1 = baker.make(
        Route,
        user=buyer,
        length=20,
        origin="Droga Dębińska 1, 61-555 Poznań",
        destination="Droga Dębińska 2, 61-555 Poznań",
        waypoints=["Droga Dębińska 3, 61-555 Poznań"],
    )
    route_2 = baker.make(
        Route,
        user=buyer,
        origin="Droga Dębińska 1, 61-555 Poznań",
        destination="Droga Dębińska 2, 61-555 Poznań",
        length=30,
    )
    delivery_address = baker.make(
        DeliveryAddress,
        company_name="Buyer Company Name",
        zip="321",
        city="Buyer City",
        street="Buyer Street",
    )

    product_1 = baker.make(
        Product, third_party_delivery=True, seller=seller_1, region=traidoo_region
    )
    product_2 = baker.make(
        Product, third_party_delivery=True, seller=seller_1, region=traidoo_region
    )
    product_3 = baker.make(
        Product, third_party_delivery=True, seller=seller_2, region=traidoo_region
    )
    order = baker.make(Order)
    order_item_1 = baker.make(
        OrderItem,
        order=order,
        product=product_1,
        delivery_address=delivery_address,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=1),
    )
    order_item_2 = baker.make(
        OrderItem,
        order=order,
        product=product_1,
        delivery_address=delivery_address,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=2),
    )
    order_item_3 = baker.make(
        OrderItem,
        order=order,
        product=product_2,
        delivery_address=delivery_address,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
    )
    order_item_4 = baker.make(
        OrderItem,
        order=order,
        product=product_3,
        delivery_address=delivery_address,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=4),
    )

    response = client_anonymous.post(
        f"/jobs/create/{order.id}", **{"HTTP_X_APPENGINE_QUEUENAME": "queue"}
    )

    assert response.status_code == 200

    jobs = Job.objects.all()
    assert len(jobs) == 2

    assert [
        job for job in jobs[0].order_items.values_list("id", flat=True).order_by("id")
    ] == [
        order_item_1.id,
        order_item_2.id,
        order_item_3.id,
    ]
    assert [
        job for job in jobs[1].order_items.values_list("id", flat=True).order_by("id")
    ] == [order_item_4.id]

    for job in jobs:
        assert not job.user

    assert Detour.objects.count() == 4

    for job in jobs:
        for route in (route_1, route_2):
            detours = Detour.objects.filter(route=route, job=job).all()
            for detour in detours:
                assert detour.route.id == route.id
                assert detour.length == (default_route_length - route.length)
                assert detour.job.id == job.id

    assert calculate_route_length_mock.call_count == 4
    assert (
        mock.call(
            route_1.origin,
            route_1.destination,
            route_1.waypoints
            + [
                order_item_1.product.seller.address_as_str,
                order_item_1.delivery_address_as_str,
            ],
        )
        in calculate_route_length_mock.call_args_list
    )
    assert (
        mock.call(
            route_1.origin,
            route_1.destination,
            route_1.waypoints
            + [
                order_item_4.product.seller.address_as_str,
                order_item_4.delivery_address_as_str,
            ],
        )
        in calculate_route_length_mock.call_args_list
    )
    assert (
        mock.call(
            route_2.origin,
            route_2.destination,
            route_2.waypoints
            + [
                order_item_1.product.seller.address_as_str,
                order_item_1.delivery_address_as_str,
            ],
        )
        in calculate_route_length_mock.call_args_list
    )
    assert (
        mock.call(
            route_2.origin,
            route_2.destination,
            route_2.waypoints
            + [
                order_item_4.product.seller.address_as_str,
                order_item_4.delivery_address_as_str,
            ],
        )
        in calculate_route_length_mock.call_args_list
    )
