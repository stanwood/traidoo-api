import datetime

import pytest
from django.conf import settings
from django.utils import timezone
from model_mommy import mommy

from items.models import Item


@pytest.mark.django_db
def test_find_unsold_product_items_run_tasks_for_sellers(
    client_anonymous, seller, send_task, traidoo_region
):
    client_anonymous.get(
        f"/orders/cron/find-unsold-items", **{"HTTP_X_APPENGINE_CRON": True}
    )
    send_task.assert_called_with(
        f"/orders/cron/find-unsold-items/{seller.id}",
        queue_name="unsold-items",
        http_method="POST",
        headers={"Region": traidoo_region.slug},
    )


@pytest.mark.django_db
def test_find_unsold_product_items(
    client_anonymous, seller, mailoutbox, traidoo_region
):
    yesterday = timezone.now().date() - datetime.timedelta(days=1)

    product_1, product_2 = mommy.make(
        "products.product", seller=seller, region=traidoo_region, _quantity=2
    )
    mommy.make(Item, product=product_1, quantity=10, latest_delivery_date=yesterday)
    mommy.make(Item, product=product_2, quantity=5, latest_delivery_date=yesterday)

    expired_products = [
        email for email in mailoutbox if email.subject == "Abgelaufene Produkte"
    ]
    assert len(expired_products) == 0
    assert Item.objects.count() == 2

    client_anonymous.post(
        f"/orders/cron/find-unsold-items/{seller.id}", **{"HTTP_X_APPENGINE_CRON": True}
    )

    expired_products = [
        email for email in mailoutbox if email.subject == "Abgelaufene Produkte"
    ]
    assert len(expired_products) == 1
    assert Item.objects.count() == 0

    mailbox = expired_products[0]
    assert mailbox.subject == "Abgelaufene Produkte"
    assert mailbox.from_email == settings.DEFAULT_FROM_EMAIL
    assert mailbox.to == [seller.email]


@pytest.mark.django_db
def test_find_unsold_product_items_dates_do_not_match(
    client_anonymous, seller, mailoutbox, traidoo_region
):
    today = timezone.now().date()
    assert len(mailoutbox) == 0

    product_1, product_2 = mommy.make(
        "products.product", seller=seller, region=traidoo_region, _quantity=2
    )
    mommy.make(Item, product=product_1, quantity=10, latest_delivery_date=today)
    mommy.make(Item, product=product_2, quantity=5, latest_delivery_date=today)

    assert Item.objects.count() == 2

    client_anonymous.post(
        f"/orders/cron/find-unsold-items/{seller.id}", **{"HTTP_X_APPENGINE_CRON": True}
    )

    assert Item.objects.count() == 2
    assert len(mailoutbox) == 0
