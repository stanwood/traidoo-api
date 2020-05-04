import random

import pytest

pytestmark = pytest.mark.django_db


def test_get_own_company_profile(client_seller, seller):
    response = client_seller.get("/users/profile/company")

    assert response.json() == {
        "companyName": seller.company_name,
        "companyType": seller.company_type,
        "iban": seller.iban,
        "companyRegistrationId": seller.company_registration_id,
        "vatId": seller.vat_id,
        "taxId": seller.tax_id,
        "isCertifiedOrganicProducer": seller.is_certified_organic_producer,
        "organicControlBody": seller.organic_control_body,
        "description": seller.description,
        "street": seller.street,
        "city": seller.city,
        "zip": seller.zip,
    }


def test_update_own_company_profile(client_seller, seller, faker):
    data = {
        "companyName": faker.company(),
        "companyType": random.choice(
            ["Einzelunternehmer", "Gewerbliche GbR", "UG (haftungsbeschränkt)"]
        ),
        "iban": faker.iban(),
        "companyRegistrationId": faker.bban(),
        "vatId": faker.iban(),
        "taxId": faker.iban(),
        "isCertifiedOrganicProducer": faker.pybool(),
        "organicControlBody": faker.bban(),
        "description": faker.paragraph(nb_sentences=3),
        "street": faker.street_address(),
        "city": faker.city(),
        "zip": faker.zipcode(),
    }

    response = client_seller.put("/users/profile/company", data)

    assert response.json() == data


def test_partially_update_own_company_profile(client_seller, seller, faker):
    data = {
        "companyName": faker.company(),
        "companyType": random.choice(
            ["Einzelunternehmer", "Gewerbliche GbR", "UG (haftungsbeschränkt)"]
        ),
        "iban": faker.iban(),
        "companyRegistrationId": faker.bban(),
        "vatId": faker.iban(),
        "taxId": faker.iban(),
        "isCertifiedOrganicProducer": faker.pybool(),
        "organicControlBody": faker.bban(),
        "description": faker.paragraph(nb_sentences=3),
        "street": faker.street_address(),
        "city": faker.city(),
        "zip": faker.zipcode(),
    }

    for key, value in data.items():
        response = client_seller.patch("/users/profile/company", data)
        assert response.json()[key] == value
