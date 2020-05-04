import pytest

pytestmark = pytest.mark.django_db


def test_get_own_personal_profile(client_seller, seller):
    response = client_seller.get("/users/profile/personal")

    assert response.json() == {
        "firstName": seller.first_name,
        "lastName": seller.last_name,
        "email": seller.email,
        "region": {
            "id": seller.region.id,
            "name": seller.region.name,
            "slug": seller.region.slug,
        },
        "birthday": seller.birthday.strftime("%Y-%m-%d"),
        "nationalityCountryCode": seller.nationality_country_code.code,
        "residenceCountryCode": seller.residence_country_code.code,
        "phone": seller.phone,
        "invoiceEmail": seller.invoice_email,
    }


def test_update_own_personal_profile(client_seller, seller, faker):
    data = {
        "firstName": faker.first_name(),
        "lastName": faker.last_name(),
        "email": faker.safe_email(),
        "birthday": faker.date(pattern="%Y-%m-%d", end_datetime=None),
        "nationalityCountryCode": faker.country_code(representation="alpha-2"),
        "residenceCountryCode": faker.country_code(representation="alpha-2"),
        "phone": faker.phone_number(),
        "invoiceEmail": faker.safe_email(),
    }

    response = client_seller.put("/users/profile/personal", data)

    expected_response = data
    expected_response["region"] = {
        "id": seller.region.id,
        "name": seller.region.name,
        "slug": seller.region.slug,
    }

    assert response.json() == expected_response


def test_partially_update_own_personal_profile(client_seller, seller, faker):
    data = {
        "firstName": faker.first_name(),
        "lastName": faker.last_name(),
        "email": faker.safe_email(),
        "birthday": faker.date(pattern="%Y-%m-%d", end_datetime=None),
        "nationalityCountryCode": faker.country_code(representation="alpha-2"),
        "residenceCountryCode": faker.country_code(representation="alpha-2"),
        "phone": faker.phone_number(),
        "invoiceEmail": faker.safe_email(),
    }

    for key, value in data.items():
        response = client_seller.patch("/users/profile/personal", data)
        assert response.json()[key] == value


def test_try_to_update_profile_region(client_seller, seller, faker):
    region = {
        "id": seller.region.id,
        "name": seller.region.name,
        "slug": seller.region.slug,
    }

    response = client_seller.patch("/users/profile/personal", {"region": 123})
    assert response.json()["region"] == region

    response = client_seller.patch("/users/profile/personal", {"region": "traidoo2"})
    assert response.json()["region"] == region

    response = client_seller.patch(
        "/users/profile/personal",
        {"region": {"id": 321, "name": "Traidoo3", "slug": "traidoo3"}},
    )
    assert response.json()["region"] == region
