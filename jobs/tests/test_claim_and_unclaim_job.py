import datetime

import pytest
from model_mommy import mommy

pytestmark = pytest.mark.django_db


def _prepare_test_data():
    user_1 = mommy.make_recipe("users.user")
    user_2 = mommy.make_recipe("users.user")
    route = mommy.make_recipe("routes.route", user=user_1)
    delivery_address = mommy.make_recipe("delivery_addresses.delivery_address")
    product = mommy.make_recipe("products.product", seller=user_2)
    order = mommy.make("orders.Order")
    order_item = mommy.make(
        "orders.OrderItem",
        delivery_address=delivery_address,
        product=product,
        latest_delivery_date=datetime.date.today() + datetime.timedelta(days=6),
        order=order,
    )
    job = mommy.make("jobs.Job", order_item=order_item, user=None)
    mommy.make("jobs.Detour", job=job, route=route)
    return user_1, user_2, job, order


def test_claim_job_success(client_buyer, api_client, settings):
    settings.FEATURES["routes"] = True

    user_1, _, job, _ = _prepare_test_data()

    api_client.force_authenticate(user=user_1)

    assert not job.user

    response = api_client.post(f"/jobs/{job.id}/claim")
    assert response.status_code == 204

    job.refresh_from_db()
    assert job.user == user_1


def test_claim_job_for_processed_order(client_buyer, api_client, settings):
    settings.FEATURES["routes"] = True

    user_1, _, job, order = _prepare_test_data()

    order.processed = True
    order.save()
    order.recalculate_items_delivery_fee()

    api_client.force_authenticate(user=user_1)

    assert not job.user

    response = api_client.post(f"/jobs/{job.id}/claim")

    assert response.status_code == 400

    job.refresh_from_db()
    assert not job.user


def test_claim_claimed_job(client_buyer, api_client, settings):
    settings.FEATURES["routes"] = True

    user_1, user_2, job, _ = _prepare_test_data()

    job.user = user_2
    job.save()

    api_client.force_authenticate(user=user_1)

    response = api_client.post(f"/jobs/{job.id}/claim")
    assert response.status_code == 400

    job.refresh_from_db()
    assert job.user == user_2


def test_unclaim_job_success(client_buyer, api_client, settings):
    settings.FEATURES["routes"] = True

    user_1, _, job, _ = _prepare_test_data()

    job.user = user_1
    job.save()

    api_client.force_authenticate(user=user_1)

    response = api_client.delete(f"/jobs/{job.id}/claim")
    assert response.status_code == 204

    job.refresh_from_db()
    assert not job.user


def test_unclaim_someone_else_job(client_buyer, api_client, settings):
    settings.FEATURES["routes"] = True

    user_1, user_2, job, _ = _prepare_test_data()

    job.user = user_2
    job.save()

    api_client.force_authenticate(user=user_1)

    response = api_client.delete(f"/jobs/{job.id}/claim")
    assert response.status_code == 400

    job.refresh_from_db()
    assert job.user == user_2
