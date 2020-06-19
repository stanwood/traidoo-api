from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
def test_password_update(client_seller, seller, mailoutbox):
    old_password = "test123"
    new_password = "Test175#"

    seller.set_password(old_password)
    seller.save()

    assert seller.check_password(old_password)
    assert not seller.check_password(new_password)

    response = client_seller.post(
        "/auth/password",
        {
            "new_password": new_password,
            "re_new_password": new_password,
            "current_password": old_password,
        },
    )

    seller.refresh_from_db()

    assert not seller.check_password(old_password)
    assert seller.check_password(new_password)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Ihr Password wurde geändert"


@pytest.mark.django_db
def test_password_update_incorrect_format(client_seller, mailoutbox):
    response = client_seller.post(
        "/auth/password",
        {
            "new_password": "test",
            "re_new_password": "incorrect",
            "current_password": "incorrect",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "currentPassword": ["The two password fields didn't match."]
    }
    assert not mailoutbox


@pytest.mark.django_db
def test_password_update_mismatch(client_seller, mailoutbox):
    response = client_seller.post(
        "/auth/password",
        {
            "new_password": "incorrect",
            "re_new_password": "incorrect2",
            "current_password": "Correct888@",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "currentPassword": ["The two password fields didn't match."]
    }
    assert not mailoutbox


@pytest.mark.django_db
def test_password_update_incorrect_current_password(client_seller, mailoutbox):
    response = client_seller.post(
        "/auth/password",
        {
            "new_password": "Correct148%",
            "re_new_password": "Correct148%",
            "current_password": "Incorrect888@",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"currentPassword": ["Invalid password."]}
    assert not mailoutbox


@pytest.mark.django_db
def test_password_update_anonymous(client_anonymous, mailoutbox):
    response = client_anonymous.post(
        "/auth/password",
        {
            "new_password": "Correct148%",
            "re_new_password": "Correct148%",
            "current_password": "Incorrect888@",
        },
    )

    assert response.status_code == 401
    assert not mailoutbox
