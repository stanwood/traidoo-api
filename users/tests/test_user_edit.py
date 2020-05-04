import pytest
from django.contrib.auth import get_user_model
from model_mommy import mommy

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_user_can_edit_second_email(client_buyer, buyer):
    second_email = "second@example.com"

    assert buyer.invoice_email != second_email

    response = client_buyer.patch(f"/users/{buyer.id}", {"invoice_email": second_email})
    assert response.json()["invoiceEmail"] == second_email

    buyer.refresh_from_db()
    assert buyer.invoice_email == second_email


def test_update_business_license(client_buyer, buyer, image_file):
    response = client_buyer.patch(
        f"/users/{buyer.id}", {"businessLicense": image_file}, format="multipart"
    )
    buyer.refresh_from_db()
    assert response.status_code == 200
    assert buyer.business_license.name.startswith(f"private/user/{buyer.id}/")
    assert buyer.business_license.name.endswith(".png")
    assert response.data["business_license"].startswith(
        f"http://testserver/users/private/user/{buyer.id}/"
    )
    assert response.data["business_license"].endswith(".png")
