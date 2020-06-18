import datetime
from unittest import mock

import pytest
from model_bakery import baker


from ..models import Detour, Job

pytestmark = pytest.mark.django_db


def test_send_jobs_notification_email_to_all_users_with_routes(
    client_anonymous, send_task, settings, traidoo_region
):
    settings.FEATURES["routes"] = True

    user_1, user_2 = baker.make_recipe(
        "users.user",
        is_email_verified=True,
        is_active=True,
        region=traidoo_region,
        _quantity=2,
    )
    baker.make_recipe("routes.route", user=user_1)

    response = client_anonymous.get(
        "/jobs/cron/notifications", **{"HTTP_X_APPENGINE_CRON": True}
    )

    assert response.status_code == 204

    assert (
        mock.call(
            f"/jobs/cron/notifications/{user_1.id}",
            headers={"Region": traidoo_region.slug},
            http_method="POST",
            queue_name="emails",
        )
        in send_task.call_args_list
    )
    assert not (
        mock.call(
            f"/jobs/cron/notifications/{user_2.id}",
            headers={"Region": traidoo_region.slug},
            http_method="POST",
            queue_name="emails",
        )
        in send_task.call_args_list
    )


def test_send_jobs_notification_email_to_user(
    client_anonymous, mailoutbox, settings, traidoo_region
):
    settings.FEATURES["routes"] = True

    user_1, user_2 = baker.make_recipe(
        "users.user", is_email_verified=True, is_active=True, _quantity=2
    )
    route = baker.make_recipe("routes.route", user=user_1)
    delivery_address = baker.make_recipe("delivery_addresses.delivery_address")
    product_1, product_2 = baker.make_recipe(
        "products.product", seller=user_2, _quantity=2
    )
    order = baker.make(
        "orders.order",
        earliest_delivery_date=(datetime.datetime.today() + datetime.timedelta(days=1)),
        buyer=user_1,
    )
    order_item_1 = baker.make(
        "orders.orderitem",
        delivery_address=delivery_address,
        product=product_1,
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=6),
        order=order,
    )
    order_item_2 = baker.make(
        "orders.orderitem",
        delivery_address=delivery_address,
        product=product_2,
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=2),
        order=order,
    )

    job_1 = baker.make(Job, order_item=order_item_1)
    job_2 = baker.make(Job, order_item=order_item_2)

    baker.make(Detour, job=job_1, route=route, length=100)
    baker.make(Detour, job=job_2, route=route, length=200)

    routes = [email for email in mailoutbox if email.subject == "Routes"]

    assert len(routes) == 0

    response = client_anonymous.post(
        f"/jobs/cron/notifications/{user_1.id}",
        **{"HTTP_X_APPENGINE_QUEUENAME": "queue"},
    )

    assert response.status_code == 204

    routes = [email for email in mailoutbox if email.subject == "Routes"]

    assert len(routes) == 1
    message = routes[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert message.to == [user_1.email]

    for job in (job_1, job_2):
        for value in (
            f"{job.order_item.quantity}x {job.order_item.product.container_type.size_class}",
            job.order_item.product.name,
            f"{job.order_item.product.seller.first_name} {job.order_item.product.seller.last_name}",
            f"{job.order_item.product.seller.city}, {job.order_item.product.seller.street}, {job.order_item.product.seller.zip}",
            f"{job.order_item.order.buyer.city}, {job.order_item.order.buyer.street}, {job.order_item.order.buyer.zip}",
            str(job.detours.first().length / 1000),
            f'{format(job.order_item.delivery_fee, ".2f")} €',
            job.order_item.order.earliest_delivery_date.strftime("%b %d"),
            job.order_item.latest_delivery_date.strftime("%b %d"),
        ):
            assert value in message.body


def test_do_not_send_empty_jobs_notification_email_to_user(
    client_anonymous, mailoutbox, settings
):
    settings.FEATURES["routes"] = True

    user = baker.make_recipe("users.user", is_email_verified=True, is_active=True)
    baker.make_recipe("routes.route", user=user)

    routes = [email for email in mailoutbox if email.subject == "Routes"]
    assert len(routes) == 0

    response = client_anonymous.post(
        f"/jobs/cron/notifications/{user.id}", **{"HTTP_X_APPENGINE_QUEUENAME": "queue"}
    )

    assert response.status_code == 204

    routes = [email for email in mailoutbox if email.subject == "Routes"]
    assert len(routes) == 0
