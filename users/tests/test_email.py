import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_user_email_in_use(client_anonymous):
    user = mommy.make(User)

    response = client_anonymous.post(f"/auth/email", {"email": user.email,},)

    assert response.json() == {"exists": True}


def test_email_not_in_use(client_anonymous):
    email = "traidoo@example.com"

    assert not User.objects.filter(email=email).first()

    response = client_anonymous.post(f"/auth/email", {"email": email,},)

    assert response.json() == {"exists": False}


def test_user_email_in_use_but_id_provided(client_anonymous):
    user = mommy.make(User)

    response = client_anonymous.post(
        f"/auth/email", {"email": user.email, "user_id": user.id,},
    )

    assert response.json() == {"exists": False}


def test_user_email_does_not_exist_but_correct_id(client_anonymous):
    user = mommy.make(User)
    email = "traidoo@example.com"

    assert not User.objects.filter(email=email).first()

    response = client_anonymous.post(
        f"/auth/email", {"email": email, "user_id": user.id,},
    )

    assert response.json() == {"exists": False}
