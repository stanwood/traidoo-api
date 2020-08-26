import pytest
from model_bakery import baker

pytestmark = pytest.mark.django_db


def test_get_global_settings(client_anonymous):
    settings = baker.make_recipe("settings.global_setting")

    response = client_anonymous.get("/global_settings")
    assert response.json() == {"productVat": settings.product_vat}
