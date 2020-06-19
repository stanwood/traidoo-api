import datetime

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
def test_delete_not_verified_users(client_anonymous):
    users = baker.make("users.user", is_email_verified=False, _quantity=2)
    emails = [user.email for user in users]

    updated_at = timezone.now() + datetime.timedelta(
        minutes=settings.UNVERIFIED_USER_LIFE_HOURS + 1
    )

    assert User.objects.filter(email__in=emails).count() == 2

    with freeze_time(updated_at):
        client_anonymous.get(
            "/users/cron/delete-not-verified-users", **{"HTTP_X_APPENGINE_CRON": True}
        )

    assert User.objects.filter(email__in=emails).count() == 0


@pytest.mark.django_db
def test_do_not_delete_verified_users(client_anonymous):
    users = baker.make("users.user", is_email_verified=True, _quantity=2)
    emails = [user.email for user in users]

    updated_at = timezone.now() + datetime.timedelta(
        minutes=settings.UNVERIFIED_USER_LIFE_HOURS + 1
    )

    assert User.objects.filter(email__in=emails).count() == 2

    with freeze_time(updated_at):
        client_anonymous.get(
            "/users/cron/delete-not-verified-users", **{"HTTP_X_APPENGINE_CRON": True}
        )

    assert User.objects.filter(email__in=emails).count() == 2


@pytest.mark.django_db
def test_do_not_delete_not_verified_users_before_given_time(client_anonymous):
    users = baker.make("users.user", is_email_verified=False, _quantity=2)
    emails = [user.email for user in users]

    updated_at = timezone.now() + datetime.timedelta(
        minutes=settings.UNVERIFIED_USER_LIFE_HOURS - 1
    )

    assert User.objects.filter(email__in=emails).count() == 2

    with freeze_time(updated_at):
        client_anonymous.get(
            "/users/cron/delete-not-verified-users", **{"HTTP_X_APPENGINE_CRON": True}
        )

    assert User.objects.filter(email__in=emails).count() == 2
