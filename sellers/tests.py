import pytest

pytestmark = pytest.mark.django_db


def test_get_seller(client_anonymous, seller):
    response = client_anonymous.get(f"/sellers/{seller.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": seller.id,
        "firstName": seller.first_name,
        "lastName": seller.last_name,
        "companyName": seller.company_name,
        "description": seller.description,
        "city": seller.city,
        "image": seller.image,
        "imageUrl": seller.image_url,
        "groups": ["seller"],
    }
