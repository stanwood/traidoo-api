import pytest


@pytest.mark.django_db
def test_resend_verification_email_user_not_verified(client_seller, seller, mailoutbox):
    seller.is_email_verified = False
    seller.save()

    response = client_seller.post("/auth/verify-email/resend")
    assert response.status_code == 204
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_resend_verification_email_user_verified(client_seller, seller, mailoutbox):
    seller.is_email_verified = True
    seller.save()

    response = client_seller.post("/auth/verify-email/resend")
    assert response.status_code == 204
    assert len(mailoutbox) == 0
