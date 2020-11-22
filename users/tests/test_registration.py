from copy import copy
from unittest import mock

import bs4
import pytest
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import reverse
from model_bakery import baker

from delivery_addresses.models import DeliveryAddress

from ..models.kyc import KycDocument

User = get_user_model()


@pytest.fixture
def user_data(image_file, cloud_storage_save, cloud_storage_url):

    yield {
        # Personal data
        "first_name": "Test",
        "last_name": "Trofimiuk",
        "email": "test@example.com",
        "phone": "999999999999",
        "password": "1234Abcd",
        "birthday": "2019-03-02",
        "nationality_country_code": "DE",
        "street": "Sesame 99",
        "residence_country_code": "DE",
        "city": "Berlin",
        "zip": "33333",
        # Company data
        "company_name": "Foo GmbH",
        "company_type": "GmbH",
        "iban": "GB33BUKB20201555555555",
        "company_registration_id": "222",
        "vat_id": "1234",
        "tax_id": "333",
        "is_certified_organic_producer": True,
        "organic_control_body": "DE-ÖKO-012",
        # Documents
        "business_license": copy(image_file),
        "image": copy(image_file),
        # KYC Documents
        "identity_proof": copy(image_file),
        "shareholder_declaration": copy(image_file),
        "articles_of_association": copy(image_file),
        "registration_proof": copy(image_file),
        "address_proof": copy(image_file),
    }


@pytest.mark.django_db
def test_register_user(client_anonymous, send_task, user_data, mailoutbox):
    users_count = User.objects.count()

    response = client_anonymous.post(
        "/registration", data=user_data, format="multipart"
    )

    assert response.status_code == 201
    assert User.objects.count() == users_count + 1

    user = User.objects.last()

    kyc_documents = {
        "identity_proof": KycDocument.Name.IDENTITY_PROOF.name,
        "shareholder_declaration": KycDocument.Name.SHAREHOLDER_DECLARATION.name,
        "articles_of_association": KycDocument.Name.ARTICLES_OF_ASSOCIATION.name,
        "registration_proof": KycDocument.Name.REGISTRATION_PROOF.name,
        "address_proof": KycDocument.Name.ADDRESS_PROOF.name,
    }

    for key, value in user_data.items():
        if key not in ("birthday", "password", "image", "business_license") + tuple(
            kyc_documents.keys()
        ):
            assert getattr(user, key) == value

    assert user.mangopay_validation_level == "light"
    assert user.check_password(user_data["password"])

    assert user.image.name.startswith(f"public/user/{user.id}/")
    assert user.image.name.endswith(".png")
    assert user.business_license.name.startswith(f"private/user/{user.id}/")
    assert user.business_license.name.endswith(".png")

    assert KycDocument.objects.count() == 5
    for key, value in kyc_documents.items():
        document = KycDocument.objects.get(user=user, name=value)
        assert document.file

    send_task.assert_called_once_with(
        f"/users/{user.id}/mangopay/create",
        http_method="POST",
        queue_name="mangopay-create-account",
        schedule_time=10,
        headers={
            "Region": user.region.slug,
            "Content-Type": "application/json",
        },
    )
    assert mailoutbox[-2].subject == "Bitte bestätigen Sie Ihre E-Mail-Adresse"
    assert mailoutbox[-2].to == [user.email]


@pytest.mark.django_db
def test_registration_missing_values(client_anonymous, send_task, mailoutbox):
    response = client_anonymous.post("/registration", {}, format="multipart")
    assert response.status_code == 400

    assert response.json() == {
        "firstName": [{"message": "This field is required.", "code": "required"}],
        "lastName": [{"message": "This field is required.", "code": "required"}],
        "email": [{"message": "This field is required.", "code": "required"}],
        "phone": [{"message": "This field is required.", "code": "required"}],
        "password": [{"message": "This field is required.", "code": "required"}],
        "birthday": [{"message": "This field is required.", "code": "required"}],
        "nationalityCountryCode": [
            {"message": "This field is required.", "code": "required"}
        ],
        "street": [{"message": "This field is required.", "code": "required"}],
        "residenceCountryCode": [
            {"message": "This field is required.", "code": "required"}
        ],
        "city": [{"message": "This field is required.", "code": "required"}],
        "zip": [{"message": "This field is required.", "code": "required"}],
        "companyName": [{"message": "This field is required.", "code": "required"}],
        "companyType": [{"message": "This field is required.", "code": "required"}],
        "taxId": [{"message": "This field is required.", "code": "required"}],
    }


@pytest.mark.django_db
def test_registration_validation(client_anonymous, send_task, mailoutbox, user_data):
    user_data["email"] = "incorrect"
    user_data["birthday"] = "2012"
    user_data["password"] = "notsecure"

    response = client_anonymous.post("/registration", user_data, format="multipart")
    assert response.status_code == 400

    assert response.json() == {
        "email": [{"message": "Enter a valid email address.", "code": "invalid"}],
        "password": [
            {
                "message": "Incorrect password format.",
                "code": "password_incorrect_format",
            }
        ],
        "birthday": [
            {
                "message": "Date has wrong format. Use one of these formats instead: YYYY-MM-DD.",
                "code": "invalid",
            }
        ],
    }

    send_task.assert_not_called()
    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_registration_activate_user(client_anonymous, send_task, user_data, mailoutbox):
    client_anonymous.post("/registration", user_data, format="multipart")

    user = User.objects.get(email=user_data["email"])
    assert user.is_active
    assert not user.is_email_verified

    assert len(mailoutbox) == 2

    assert mailoutbox[1].subject == "Neuer Nutzer registriert"
    assert user.email not in mailoutbox[1].to

    assert mailoutbox[0].subject == "Bitte bestätigen Sie Ihre E-Mail-Adresse"
    assert mailoutbox[0].to == [user.email]

    soup = bs4.BeautifulSoup(mailoutbox[0].body, features="html.parser")
    links = [link["href"] for link in soup("a") if "href" in link.attrs]
    activation_link = [link for link in links if "registration" in link][0]
    uid, token = activation_link.replace(
        f"https://{Site.objects.get_current().domain}/registration/", ""
    ).split("/")

    user.mangopay_user_id = "mangopay-user-id"
    user.save()

    response = client_anonymous.post("/auth/verify-email", {"uid": uid, "token": token})
    assert response.status_code == 204

    user.refresh_from_db()
    assert user.is_active
    assert user.is_email_verified

    send_task.assert_called_with(
        "/mangopay/tasks/create-wallet",
        headers={"Region": "traidoo", "Content-Type": "application/json"},
        http_method="POST",
        payload={"user_id": user.id},
        queue_name="mangopay-create-wallet",
        schedule_time=5,
    )


@pytest.mark.django_db
def test_registration_set_a_proper_region(client_anonymous, user_data):
    region = baker.make_recipe("common.region", name="Test Region")
    response = client_anonymous.post(
        "/registration",
        data=user_data,
        format="multipart",
        **{"HTTP_REGION": region.slug},
    )

    assert response.status_code == 201
    assert User.objects.last().region.name == region.name


@pytest.mark.django_db
def test_registration_company_id_required(client_anonymous, user_data, settings):
    settings.FEATURES["company_registration_id"] = True
    del user_data["company_registration_id"]

    region = baker.make_recipe("common.region", name="Test Region")
    response = client_anonymous.post(
        "/registration",
        data=user_data,
        format="multipart",
        **{"HTTP_REGION": region.slug},
    )

    assert response.status_code == 400
    assert response.json() == {
        "companyRegistrationId": [
            {"message": "This field is required.", "code": "required"}
        ]
    }


@pytest.mark.django_db
def test_registration_company_id_not_required(client_anonymous, user_data, settings):
    settings.FEATURES["company_registration_id"] = False
    del user_data["company_registration_id"]

    region = baker.make_recipe("common.region", name="Test Region")
    response = client_anonymous.post(
        "/registration",
        data=user_data,
        format="multipart",
        **{"HTTP_REGION": region.slug},
    )

    assert response.status_code == 201


@pytest.mark.django_db
def test_registration_create_delivery_address(client_anonymous, user_data):
    assert DeliveryAddress.objects.count() == 0

    region = baker.make_recipe("common.region", name="Test Region")
    response = client_anonymous.post(
        "/registration",
        data=user_data,
        format="multipart",
        **{"HTTP_REGION": region.slug},
    )

    assert response.status_code == 201

    delivery_address = DeliveryAddress.objects.get()
    assert delivery_address.company_name == user_data["company_name"]
    assert delivery_address.city == user_data["city"]
    assert delivery_address.zip == user_data["zip"]
    assert delivery_address.street == user_data["street"]


@pytest.mark.django_db
def test_registration_unique_email(client_anonymous, user_data, buyer):
    user_data["email"] = buyer.email

    region = baker.make_recipe("common.region", name="Test Region")
    response = client_anonymous.post(
        "/registration",
        data=user_data,
        format="multipart",
        **{"HTTP_REGION": region.slug},
    )

    assert response.status_code == 400
    assert response.json() == {
        "email": [{"message": "This field must be unique.", "code": "unique"}]
    }


def test_send_new_user_email_to_admins(db, client_anonymous, user_data, mailoutbox):
    client_anonymous.post("/registration", data=user_data, format="multipart")

    users_edit_admin_url = reverse("admin:users_user_changelist")
    assert f"https://testserver{users_edit_admin_url}" in mailoutbox[1].body
    assert "test1@example.com" in mailoutbox[1].to
    assert "test2@example.com" in mailoutbox[1].to
