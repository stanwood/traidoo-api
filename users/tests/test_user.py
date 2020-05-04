import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy


User = get_user_model()

pytestmark = pytest.mark.django_db


def test_user_valid_iban():
    user = mommy.make(User, iban="-")
    assert not user.has_valid_iban
    user = mommy.make(User, iban="DE30170560600101004672")
    assert user.has_valid_iban


@pytest.mark.django_db
def test_get_own_profile(client_seller, seller):
    response = client_seller.get("/users/profile/me")
    assert response.json() == {"id": seller.id, "groups": ["seller"]}


@pytest.mark.django_db
def test_someone_else_profile(client_seller, seller, buyer):
    response = client_seller.get(f"/users/profile/{buyer.id}")
    # TODO: temporary solution, return 400/404
    assert response.json() == {"id": seller.id, "groups": ["seller"]}
