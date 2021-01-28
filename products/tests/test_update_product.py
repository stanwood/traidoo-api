import json

import pytest
from model_bakery import baker

from products.models import Product


@pytest.mark.parametrize("base_unit", ["volume", "weight"])
@pytest.mark.django_db
def test_update_product_with_valid_base_unit_options(
    seller, admin, client_admin, base_unit, traidoo_region
):
    product = baker.make(Product, region=traidoo_region)

    response = client_admin.patch(
        f"/products/{product.id}",
        {"seller_id": seller.id, "base_unit": base_unit, "item_quantity": 1.2},
        format="multipart",
    )

    parsed_response = response.json()

    assert response.status_code == 200
    assert parsed_response["baseUnit"] == base_unit
    assert parsed_response["itemQuantity"] == 1.2


@pytest.mark.django_db
def test_update_product_with_invalid_base_unit_options(
    seller, admin, client_admin, traidoo_region
):
    product = baker.make(Product, region=traidoo_region)

    response = client_admin.patch(
        f"/products/{product.id}",
        {"seller_id": seller.id, "base_unit": "height", "item_quantity": 1.2},
        format="multipart",
    )

    parsed_response = response.json()

    assert response.status_code == 400
    assert parsed_response == {
        "baseUnit": [
            {"code": "invalid_choice", "message": '"height" is not a valid choice.'}
        ]
    }


@pytest.mark.django_db
def test_remove_product_regions(seller, admin, client_seller, traidoo_region):
    region = baker.make("common.region")
    product = baker.make(
        Product, region=traidoo_region, regions=[region], seller=seller
    )
    assert product.regions.count() == 1

    response = client_seller.patch(
        f"/products/{product.id}",
        {"regions": "", "name": "test123123"},
        format="multipart",
    )
    assert response.status_code == 200
    assert product.regions.count() == 0


def test_edit_product_not_owned_by_me(seller, admin, client_seller, traidoo_region):
    other_seller = baker.make("users.user")
    product = baker.make(
        "products.product", region=traidoo_region, seller=other_seller, price=2
    )

    response = client_seller.patch(
        f"/products/{product.id}",
        {"price": 1},
        format="multipart",
    )
    product.refresh_from_db()
    assert response.status_code == 403
    assert product.price == 2
