import json

import pytest
from model_mommy import mommy
from taggit.models import Tag

from categories.models import Category
from containers.models import Container
from delivery_options.models import DeliveryOption


@pytest.mark.parametrize(
    "request_user, request_user_groups, product_user, response_status, response_message",
    [
        (
            "admin",
            "admin",
            None,
            400,
            {"sellerId": [{"message": "This field is required.", "code": "invalid"}]},
        ),
        ("admin", "admin,seller", None, 201, None),
        (
            "admin",
            "admin,buyer",
            None,
            400,
            {"sellerId": [{"message": "This field is required.", "code": "invalid"}]},
        ),
        ("admin", "admin,seller,buyer", None, 201, None),
        ("admin", "admin", "seller", 201, None),
        ("admin", "admin,seller", "seller", 201, None),
        ("admin", "admin,buyer", "seller", 201, None),
        ("admin", "admin,seller,buyer", "seller", 201, None),
        ("seller", "seller", None, 201, None),
        ("seller", "seller", "seller", 201, None),
        (
            "seller",
            "seller",
            "buyer",
            403,
            {
                "sellerId": [
                    {
                        "code": "permission_denied",
                        "message": "Only admin can use this field.",
                    }
                ]
            },
        ),
        (
            "buyer",
            "buyer",
            None,
            403,
            {
                "code": "permission_denied",
                "message": "You do not have permission to perform this action.",
            },
        ),
    ],
)
@pytest.mark.django_db
def test_add_product_permissions(
    seller,
    buyer,
    admin,
    client_seller,
    client_buyer,
    client_admin,
    admin_group,
    seller_group,
    buyer_group,
    image_file,
    cloud_storage_save,
    cloud_storage_url,
    request_user,
    request_user_groups,
    product_user,
    response_status,
    response_message,
    traidoo_region,
):
    clients = {"admin": client_admin, "seller": client_seller, "buyer": client_buyer}
    users = {"admin": admin, "seller": seller, "buyer": buyer}
    groups = {
        "admin": [admin_group],
        "seller": [seller_group],
        "buyer": [buyer_group],
        "admin,seller": [admin_group, seller_group],
        "admin,buyer": [admin_group, buyer_group],
        "admin,seller,buyer": [admin_group, seller_group, buyer_group],
    }

    client = clients.get(request_user)
    client_user = users.get(request_user)
    product_owner = users.get(product_user or request_user)

    client_user.is_active = True
    client_user.is_email_verified = True
    client_user.groups.set(groups.get(request_user_groups))
    client_user.save()

    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    payload = {
        "name": "Test",
        "description": "Test",
        "image": image_file,
        "category_id": category.id,
        "amount": 1,
        "vat": 1,
        "container_type_id": container.id,
        "delivery_options_ids": [delivery_option.id],
        "price": 100,
        "region_id": traidoo_region.id,
    }

    if product_user:
        payload["seller_id"] = product_owner.id

    response = client.post("/products", payload, format="multipart")

    assert response.status_code == response_status

    if response_message:
        assert response.json() == response_message
    else:
        assert response.json()["seller"]["id"] == product_owner.id


@pytest.mark.django_db
def test_add_product_seller(
    seller,
    client_seller,
    image_file,
    cloud_storage_save,
    cloud_storage_url,
    traidoo_region,
):
    seller.is_active = True
    seller.is_email_verified = True
    seller.save()

    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option_1 = mommy.make(DeliveryOption, id=1)
    delivery_option_2 = mommy.make(DeliveryOption, id=2)
    tag_1 = mommy.make(Tag)
    tag_2 = mommy.make(Tag)

    response = client_seller.post(
        "/products",
        {
            "name": "Test",
            "description": "Test",
            "tags": json.dumps([tag_1.id, tag_2.id]),
            "image": image_file,
            "category_id": category.id,
            "amount": 1,
            "vat": 1,
            "container_type_id": container.id,
            "delivery_options_ids": [delivery_option_1.id, delivery_option_2.id],
            "price": 100,
            "delivery_requirements": "Temperature: -10",
            "third_party_delivery": True,
            "region_id": traidoo_region.id,
        },
        format="multipart",
    )

    assert response.json()["seller"]["id"] == seller.id
    assert response.json()["deliveryRequirements"] == "Temperature: -10"
    assert response.json()["thirdPartyDelivery"] is True
    assert len(response.json()["tags"]) == 2
    assert len(response.json()["deliveryOptions"]) == 2


@pytest.mark.django_db
def test_add_product_as_admin_without_seller_id(
    seller,
    admin,
    client_admin,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    product_data = {
        "name": "Test",
        "description": "Test",
        "image": image_file,
        "category_id": category.id,
        "amount": 1,
        "vat": 1,
        "container_type_id": container.id,
        "delivery_options_ids": [delivery_option.id],
        "price": 100,
        "region_id": traidoo_region.id,
    }

    admin.is_active = True
    admin.is_email_verified = True
    admin.save()

    response = client_admin.post("/products", product_data, format="multipart")

    assert response.json() == {
        "sellerId": [{"message": "This field is required.", "code": "invalid"}]
    }


@pytest.mark.django_db
def test_add_product_as_admin_and_seller(
    seller,
    admin,
    client_admin,
    seller_group,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    product_data = {
        "name": "Test",
        "description": "Test",
        "image": image_file,
        "category_id": category.id,
        "amount": 1,
        "vat": 1,
        "container_type_id": container.id,
        "delivery_options_ids": [delivery_option.id],
        "price": 100,
        "region_id": traidoo_region.id,
    }

    admin.is_active = True
    admin.is_email_verified = True
    admin.groups.add(seller_group)
    admin.save()

    response = client_admin.post("/products", product_data, format="multipart")

    assert response.status_code == 201
    assert response.json()["seller"]["id"] == admin.id


@pytest.mark.django_db
def test_admin_can_add_product_for_another_user(
    seller,
    admin,
    client_admin,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    product_data = {
        "name": "Test",
        "description": "Test",
        "image": image_file,
        "category_id": category.id,
        "amount": 1,
        "vat": 1,
        "container_type_id": container.id,
        "delivery_options_ids": [delivery_option.id],
        "price": 100,
        "seller_id": seller.id,
        "region_id": traidoo_region.id,
    }

    admin.is_active = True
    admin.is_email_verified = True
    admin.save()

    response = client_admin.post("/products", product_data, format="multipart")

    assert response.status_code == 201
    assert response.json()["seller"]["id"] == seller.id


@pytest.mark.parametrize(
    "base_unit, expected_status_code", [("volume", 201), ("weight", 201)]
)
@pytest.mark.django_db
def test_add_product_with_valid_base_unit_options(
    seller,
    admin,
    client_admin,
    base_unit,
    expected_status_code,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)
    tag = mommy.make(Tag)

    product_data = {
        "name": "Test",
        "description": "Test",
        "image": image_file,
        "category_id": category.id,
        "amount": 1,
        "vat": 1,
        "container_type_id": container.id,
        "delivery_options_ids": [delivery_option.id],
        "price": 100,
        "seller_id": seller.id,
        "item_quantity": 1.2,
        "base_unit": base_unit,
        "region_id": traidoo_region.id,
    }

    admin.is_active = True
    admin.is_email_verified = True
    admin.save()

    response = client_admin.post("/products", product_data, format="multipart")
    parsed_response = response.json()

    assert response.status_code == expected_status_code
    assert parsed_response["baseUnit"] == base_unit
    assert parsed_response["itemQuantity"] == 1.2


@pytest.mark.django_db
def test_add_product_with_invalid_base_unit_options(
    seller,
    admin,
    client_admin,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    product_data = {
        "name": "Test",
        "description": "Test",
        "image": image_file,
        "category_id": category.id,
        "amount": 1,
        "vat": 1,
        "container_type_id": container.id,
        "delivery_options_ids": [delivery_option.id],
        "price": 100,
        "sellerId": seller.id,
        "item_quantity": 1.2,
        "base_unit": "some-invalid-value",
        "region_id": traidoo_region.id,
    }

    admin.is_active = True
    admin.is_email_verified = True
    admin.save()

    response = client_admin.post("/products", product_data, format="multipart")
    parsed_response = response.json()

    assert response.status_code == 400
    assert parsed_response == {
        "baseUnit": [
            {
                "code": "invalid_choice",
                "message": '"some-invalid-value" is not a valid choice.',
            }
        ]
    }


@pytest.mark.django_db
def test_add_product_with_container_description(
    seller,
    client_seller,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    seller.is_active = True
    seller.is_email_verified = True
    seller.save()

    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    response = client_seller.post(
        "/products",
        {
            "name": "Test",
            "description": "Test",
            "image": image_file,
            "category_id": category.id,
            "amount": 1,
            "vat": 1,
            "container_type_id": container.id,
            "container_description": "Container Description",
            "delivery_options_ids": [delivery_option.id],
            "price": 100,
            "delivery_requirements": "Temperature: -10",
            "third_party_delivery": True,
            "region_id": traidoo_region.id,
        },
        format="multipart",
    )

    assert response.status_code == 201

    parsed_response = response.json()

    assert parsed_response["containerDescription"] == "Container Description"


@pytest.mark.django_db
def test_add_product_with_grazning_animal_and_gmo_free(
    seller,
    client_seller,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    seller.is_active = True
    seller.is_email_verified = True
    seller.save()

    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    response = client_seller.post(
        "/products",
        {
            "name": "Test",
            "description": "Test",
            "image": image_file,
            "category_id": category.id,
            "amount": 1,
            "vat": 1,
            "container_type_id": container.id,
            "delivery_options_ids": [delivery_option.id],
            "price": 100,
            "is_grazing_animal": True,
            "is_gmo_free": True,
            "region_id": traidoo_region.id,
        },
        format="multipart",
    )

    assert response.status_code == 201

    parsed_response = response.json()

    assert parsed_response["seller"]["id"] == seller.id
    assert parsed_response["isGrazingAnimal"]
    assert parsed_response["isGmoFree"]


@pytest.mark.django_db
def test_add_product_with_available_regions(
    seller,
    client_seller,
    image_file,
    cloud_storage_url,
    cloud_storage_save,
    traidoo_region,
):
    seller.is_active = True
    seller.is_email_verified = True
    seller.save()

    category = mommy.make(Category)
    container = mommy.make(Container)
    delivery_option = mommy.make(DeliveryOption, id=1)

    region_1 = mommy.make("common.region", id=1001, name="Test 1")
    region_2 = mommy.make("common.region", id=1002, name="Test 2")
    region_3 = mommy.make("common.region", id=1003, name="Test 3")

    response = client_seller.post(
        "/products",
        {
            "name": "Test",
            "description": "Test",
            "image": image_file,
            "category_id": category.id,
            "amount": 1,
            "vat": 1,
            "container_type_id": container.id,
            "delivery_options_ids": [delivery_option.id],
            "price": 100,
            "isGrazingAnimal": True,
            "isGmoFree": True,
            "region_id": traidoo_region.id,
            "regions": [region_1.id, region_2.id, region_3.id],
        },
        format="multipart",
    )

    assert response.status_code == 201

    parsed_response = response.json()

    assert parsed_response["regions"] == [
        {"id": 1001, "name": "Test 1", "slug": "test-1"},
        {"id": 1002, "name": "Test 2", "slug": "test-2"},
        {"id": 1003, "name": "Test 3", "slug": "test-3"},
    ]
