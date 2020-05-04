from unittest import mock

import pytest


@pytest.mark.django_db
def test_try_to_update_user_company_type_to_natural_user(seller, client_seller):
    seller.company_type = "GmbH"
    seller.save()

    response = client_seller.patch(
        f"/users/{seller.id}", {"company_type": "Einzelunternehmer"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "companyType": [{"code": "invalid", "message": "Change not allowed."}]
    }


@pytest.mark.django_db
def test_user_change_company_type(seller, client_seller):
    seller.company_type = "GmbH"
    seller.save()

    response = client_seller.patch(f"/users/{seller.id}", {"company_type": "OHG"})

    assert response.status_code == 200
    assert response.json()["companyType"] == "OHG"

    seller.refresh_from_db()
    seller.company_type == "OHG"
