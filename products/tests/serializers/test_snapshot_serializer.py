import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_product_snapshot_without_user_password():
    user = baker.make_recipe("users.user", password="123")
    product = baker.make_recipe("products.product", seller=user)
    snapshot = product.create_snapshot()
    assert not snapshot["seller"].get("password")
