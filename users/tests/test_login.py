import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy

User = get_user_model()


@pytest.mark.django_db
def test_cannot_login_to_different_region(client_anonymous):
    test_password = "Traidoo123"
    region_1 = mommy.make("common.region", name="Test Region 1")
    region_2 = mommy.make("common.region", name="Test Region 2")
    user = mommy.make("users.user", region=region_1, is_active=True)
    user.set_password(test_password)
    user.save()

    successful_response = client_anonymous.post(
        "/auth/token",
        {"email": user.email, "password": test_password},
        **{"HTTP_REGION": region_1.slug}
    )

    assert successful_response.status_code == 200

    failed_response = client_anonymous.post(
        "/auth/token",
        {"email": user.email, "password": test_password},
        **{"HTTP_REGION": region_2.slug}
    )

    assert failed_response.status_code == 401
