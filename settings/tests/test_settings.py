import pytest
from model_bakery import baker

pytestmark = pytest.mark.django_db


def test_get_settings(client_anonymous):
    settings = baker.make_recipe("settings.setting")

    response = client_anonymous.get(
        "/settings", **{"HTTP_REGION": settings.region.slug}
    )

    assert response.json() == {
        "minPurchaseValue": float(settings.min_purchase_value),
    }
