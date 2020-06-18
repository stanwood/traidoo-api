from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
def test_password_reset_confirm_incorrect_uid(client_anonymous, mailoutbox):
    user = baker.make(User)

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0

    data = {
        "uid": f"incorrect-{user.generate_uid()}",
        "token": user.generate_token(),
        "new_password": "Traidoo123",
    }

    response = client_anonymous.post("/auth/password-set", data)
    assert response.json() == {"uid": ["Invalid user id or user doesn't exist."]}
    assert response.status_code == 400

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0


@pytest.mark.django_db
def test_password_reset_confirm_incorrect_token(client_anonymous, mailoutbox):
    user = baker.make(User)

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0

    data = {
        "uid": user.generate_uid(),
        "token": f"incorrect-{user.generate_token()}",
        "new_password": "Traidoo123",
    }

    response = client_anonymous.post("/auth/password-set", data)
    assert response.json() == {"token": ["Invalid token for given user."]}
    assert response.status_code == 400

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0


@pytest.mark.django_db
def test_password_reset_confirm_incorrect_password_format(client_anonymous, mailoutbox):
    user = baker.make(User)

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0

    data = {
        "uid": user.generate_uid(),
        "token": user.generate_token(),
        "new_password": "Traidoo",
    }

    response = client_anonymous.post("/auth/password-set", data)
    assert response.json() == {"newPassword": ["Incorrect password format."]}
    assert response.status_code == 400

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0


@pytest.mark.django_db
def test_password_reset_confirm(client_anonymous, mailoutbox, traidoo_region):
    user = baker.make(User, region=traidoo_region)

    emails = [
        email for email in mailoutbox if email.subject == "Ihr Password wurde geändert"
    ]
    assert len(emails) == 0

    data = {
        "uid": user.generate_uid(),
        "token": user.generate_token(),
        "new_password": "Traidoo123",
    }

    response = client_anonymous.post("/auth/password-set", data)
    assert response.status_code == 204

    assert mailoutbox[-1].to == [user.email]
    assert mailoutbox[-1].subject == "Ihr Password wurde geändert"
    assert mailoutbox[-1].from_email == settings.DEFAULT_FROM_EMAIL

    user.refresh_from_db()
    user.is_email_verified = True
    user.is_active = True
    user.save()

    response = client_anonymous.post(
        "/auth/token", {"email": user.email, "password": "Traidoo123"}
    )

    assert response.status_code == 200
