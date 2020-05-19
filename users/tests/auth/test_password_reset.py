import pytest


@pytest.mark.django_db
def test_password_reset(client_anonymous, seller, mailoutbox):
    response = client_anonymous.post("/auth/password-reset", {"email": seller.email})
    assert response.status_code == 204
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_password_reset_user_does_not_exist(client_anonymous, mailoutbox):
    response = client_anonymous.post(
        "/auth/password-reset", {"email": "incorrect@example.com"}
    )
    assert response.status_code == 204
    assert len(mailoutbox) == 0
