import pytest
from model_bakery import baker

from products.models import Product

pytestmark = pytest.mark.django_db


def test_fallback_to_image_url(client_admin, traidoo_region):
    product = baker.make("products.product", image_url="foo.png", region=traidoo_region)
    response = client_admin.get("/products/{}".format(product.id))
    assert response.data["image"] == "foo.png"


def test_get_product(
    buyer, client_buyer, traidoo_region, delivery_options, traidoo_settings
):
    seller = baker.make(
        "users.user",
        business_license=None,
        city="Test City",
        company_name="Test Company",
        description="Test description of the test company",
        first_name="Test first name",
        id=4567,
        id_photo=None,
        image=None,
        last_name="Test last name",
    )

    category = baker.make_recipe(
        "categories.category",
        default_vat=None,
        id=123,
        name="Test category",
        ordering=None,
        parent=None,
    )

    container = baker.make(
        "containers.container",
        delivery_fee=None,
        deposit=None,
        id=345,
        image=None,
        image_url=None,
        size_class="Test size class",
        standard=None,
        volume=456.78,
    )

    product = baker.make(
        "products.product",
        amount=123.45,
        description="Test description of the test product",
        id=98765,
        image=None,
        is_gluten_free=False,
        is_gmo_free=False,
        is_grazing_animal=False,
        is_organic=False,
        is_vegan=False,
        name="Test Product",
        price=99.98,
        unit=None,
        vat=19,
        seller=seller,
        category=category,
        container_type=container,
        region=traidoo_region,
        delivery_options=delivery_options,
        sellers_product_identifier="test123",
        ean13="12345678",
        ean8="12345678",
    )
    product.tags.add("tag1")

    response = client_buyer.get(f"/products/{product.id}")

    region_settings = traidoo_region.settings.first()

    assert region_settings.central_logistics_company
    assert response.json() == {
        "amount": 123.45,
        "category": {
            "defaultVat": None,
            "icon": {
                "id": category.icon.id,
                "iconUrl": category.icon.icon_url,
                "name": category.icon.name,
            },
            "id": 123,
            "name": "Test category",
            "ordering": None,
            "parent": None,
        },
        "containerType": {
            "deliveryFee": None,
            "deposit": None,
            "id": 345,
            "image": None,
            "imageUrl": None,
            "sizeClass": "Test size class",
            "standard": None,
            "volume": 456.78,
        },
        "delivery": {"logistics": 351.76, "pickup": 0.0, "seller": 0.0},
        "deliveryCharge": 0.0,
        "deliveryOptions": [
            {"id": 0, "name": "traidoo"},
            {"id": 1, "name": "seller"},
            {"id": 2, "name": "buyer"},
        ],
        "description": "Test description of the test product",
        "id": 98765,
        "image": None,
        "isGlutenFree": False,
        "isGmoFree": False,
        "isGrazingAnimal": False,
        "isOrganic": False,
        "isVegan": False,
        "itemsAvailable": None,
        "name": "Test Product",
        "price": 99.98,
        "region": {
            "id": traidoo_region.id,
            "name": traidoo_region.name,
            "slug": traidoo_region.slug,
        },
        "regions": [],
        "seller": {
            "businessLicense": None,
            "city": "Test City",
            "companyName": "Test Company",
            "description": "Test description of the test company",
            "firstName": "Test first name",
            "id": 4567,
            "idPhoto": None,
            "image": None,
            "lastName": "Test last name",
        },
        "unit": None,
        "vat": 19.0,
        "tags": [{"id": product.tags.first().id, "name": "tag1", "slug": "tag1",}],
        "sellersProductIdentifier": "test123",
        "thirdPartyDelivery": False,
        "ean13": "12345678",
        "ean8": "12345678",
    }


def test_get_product_no_central_logistic_company(
    buyer, client_buyer, traidoo_region, delivery_options, traidoo_settings
):
    traidoo_settings.central_logistics_company = False
    traidoo_settings.save()

    seller = baker.make(
        "users.user",
        business_license=None,
        city="Test City",
        company_name="Test Company",
        description="Test description of the test company",
        first_name="Test first name",
        id=4567,
        id_photo=None,
        image=None,
        last_name="Test last name",
    )

    category = baker.make_recipe(
        "categories.category",
        default_vat=None,
        id=123,
        name="Test category",
        ordering=None,
        parent=None,
    )

    container = baker.make(
        "containers.container",
        delivery_fee=None,
        deposit=None,
        id=345,
        image=None,
        image_url=None,
        size_class="Test size class",
        standard=None,
        volume=456.78,
    )

    product = baker.make(
        "products.product",
        amount=123.45,
        description="Test description of the test product",
        id=98765,
        image=None,
        is_gluten_free=False,
        is_gmo_free=False,
        is_grazing_animal=False,
        is_organic=False,
        is_vegan=False,
        name="Test Product",
        price=99.98,
        unit=None,
        vat=19,
        seller=seller,
        category=category,
        container_type=container,
        region=traidoo_region,
        delivery_options=delivery_options,
    )

    response = client_buyer.get(f"/products/{product.id}")
    assert response.status_code == 200

    region_settings = traidoo_region.settings.first()
    assert not region_settings.central_logistics_company

    product_delivery_options = product.delivery_options.order_by("id").values(
        "id", "name"
    )
    assert list(product_delivery_options) == [
        {"id": 0, "name": "traidoo"},
        {"id": 1, "name": "seller"},
        {"id": 2, "name": "buyer"},
    ]

    parsed_response = response.json()
    assert parsed_response["deliveryOptions"] == [
        {"id": 1, "name": "seller"},
        {"id": 2, "name": "buyer"},
    ]


def test_get_products(client_buyer, traidoo_region):
    region_1 = baker.make("common.region", name="Test 1")
    region_2 = baker.make("common.region", name="Test 2")
    region_3 = baker.make("common.region", name="Test 3")

    # Products from regions other than current
    for _ in range(20):
        baker.make("products.product", region=region_3, regions=[traidoo_region])
        baker.make("products.product", region=region_2, regions=[traidoo_region])
        baker.make("products.product", region=region_1, regions=[traidoo_region])

        # Products form region "Test 3" but not available in traidoo region
        baker.make("products.product", region=region_1, regions=[])

    # Products from MsSwiss region
    for _ in range(100):
        baker.make("products.product", region=traidoo_region)

    assert Product.objects.count() == 180

    first_page = client_buyer.get(
        "/products",
        data={"offset": 0, "limit": 100},
        **{"HTTP_REGION": traidoo_region.slug},
    )

    assert first_page.status_code == 200

    parsed_response = first_page.json()

    # Total products
    assert parsed_response["count"] == 160

    # First page (100 products) should be form traidoo region
    assert all(
        [
            product["region"]["id"] == traidoo_region.id
            for product in parsed_response["results"]
        ]
    )

    second_page = client_buyer.get(
        "/products",
        data={"offset": 100, "limit": 100},
        **{"HTTP_REGION": traidoo_region.slug},
    )

    assert second_page.status_code == 200

    parsed_response = second_page.json()

    # First page (100 products) should be form traidoo region
    assert all(
        [
            product["region"]["id"] != traidoo_region.id
            for product in parsed_response["results"]
        ]
    )
