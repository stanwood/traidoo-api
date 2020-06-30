import datetime
from decimal import Decimal
from io import BytesIO
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils import timezone
from faker import Faker
from model_bakery import baker, random_gen
from PIL import Image
from rest_framework.test import APIClient

from categories.models import Category
from common.models import Region
from delivery_addresses.models import DeliveryAddress
from delivery_options.models import DeliveryOption
from documents import factories
from items.models import Item
from settings.models import Setting


@pytest.fixture(scope="session")
def faker():
    yield Faker()


@pytest.fixture
def traidoo_region(db):
    region, _created = Region.objects.get_or_create(name="traidoo")
    region.slug = "traidoo"
    region.website_slogan = "MCS Website Slogan"
    region.mail_footer = "<p>This is my footer</p>"
    region.save()
    yield region


@pytest.fixture
def neighbour_region(db):
    region, _created = Region.objects.get_or_create(name="neighbour")
    region.slug = "neighbour"
    region.website_slogan = "We are neighbours"
    region.mail_footer = "<p>This is neighbour footer</p>"
    region.save()
    yield region


@pytest.fixture
def client(traidoo_region):
    client = APIClient(**{"HTTP_REGION": traidoo_region.slug})
    client.force_authenticate()
    yield client


@pytest.fixture
def api_client(traidoo_region):
    client = APIClient(**{"HTTP_REGION": traidoo_region.slug})
    yield client


@pytest.fixture
def client_buyer(buyer, traidoo_region):
    client = APIClient(**{"HTTP_REGION": traidoo_region.slug})
    client.force_authenticate(user=buyer)
    yield client


@pytest.fixture
def client_anonymous(traidoo_region):
    client = APIClient(**{"HTTP_REGION": traidoo_region.slug})
    yield client


@pytest.fixture
def client_seller(seller, traidoo_region):
    client = APIClient(**{"HTTP_REGION": traidoo_region.slug})
    client.force_authenticate(user=seller)
    yield client


@pytest.fixture
def client_admin(admin, traidoo_region):
    client = APIClient(**{"HTTP_REGION": traidoo_region.slug})
    client.force_authenticate(user=admin)
    client.force_login(user=admin)
    yield client


@pytest.fixture(autouse=True, scope="function")
def send_task():
    with mock.patch("core.tasks.mixin.TasksMixin.send_task") as send_task_mock:
        yield send_task_mock


@pytest.fixture
def logistics_user(traidoo_region):
    yield baker.make(
        "users.user",
        email=settings.LOGISTICS_EMAIL,
        mangopay_user_id="30",
        company_name="Traidoo",
        is_email_verified=True,
        region=traidoo_region,
    )


@pytest.fixture
def platform_user(traidoo_region, admin_group):
    yield baker.make(
        "users.user",
        region=traidoo_region,
        email="platform-local@example.com",
        mangopay_user_id="40",
        company_name="Traidoo",
        is_email_verified=True,
        groups=[admin_group],
        is_staff=True,
    )


@pytest.fixture(autouse=True)
def central_platform_user(db, traidoo_region):
    yield baker.make_recipe(
        "users.user",
        email=settings.PLATFORM_EMAIL,
        mangopay_user_id="50",
        company_name="Traidoo",
        is_email_verified=True,
        region=traidoo_region,
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture(autouse=True)
def traidoo_settings(traidoo_region, platform_user, logistics_user):
    yield baker.make(
        Setting,
        charge=10,
        mc_swiss_delivery_fee_vat=19,
        platform_fee_vat=19,
        transport_insurance=4,
        deposit_vat=19,
        min_purchase_value=50,
        region=traidoo_region,
        platform_user=platform_user,
        logistics_company=logistics_user,
        central_share=Decimal("40"),
        enable_platform_fee_share=True,
    )


@pytest.fixture(autouse=True)
def neighbour_settings(neighbour_region):
    platform_user = baker.make_recipe(
        "users.user", company_name="Neighbour Local Platform"
    )
    logistics_user = baker.make_recipe(
        "users.user", company_name="Neighbour Logistics", region=neighbour_region
    )

    yield baker.make(
        Setting,
        charge=10,
        mc_swiss_delivery_fee_vat=19,
        platform_fee_vat=19,
        transport_insurance=4,
        deposit_vat=19,
        min_purchase_value=50,
        region=neighbour_region,
        platform_user=platform_user,
        logistics_company=logistics_user,
        central_share=Decimal("40"),
        enable_platform_fee_share=True,
    )


@pytest.fixture
def buyer_group():
    yield baker.make(Group, name="buyer")


@pytest.fixture
def buyer(buyer_group, traidoo_region):
    yield baker.make_recipe(
        "users.user",
        groups=[buyer_group],
        company_name="ACME",
        is_cooperative_member=True,
        region=traidoo_region,
        mangopay_user_id="mangopay-buyer-1",
        is_email_verified=True,
    )


@pytest.fixture
def seller_group():
    yield baker.make(Group, name="seller")


@pytest.fixture
def admin_group(db):
    yield baker.make(Group, name="admin")


@pytest.fixture(autouse=True)
def admin(admin_group, traidoo_region):
    yield baker.make(
        "users.user",
        groups=[admin_group],
        is_staff=True,
        is_superuser=True,
        region=traidoo_region,
    )


@pytest.fixture
def seller(seller_group, traidoo_region):
    yield baker.make_recipe(
        "users.user",
        groups=[seller_group],
        mangopay_user_id="10",
        company_name="Best apples",
        email="best@apples.de",
        is_email_verified=True,
        is_cooperative_member=True,
        region=traidoo_region,
    )


@pytest.yield_fixture
def categories():
    yield [
        baker.make(Category, name="Fruits", ordering=1, default_vat=19),
        baker.make(Category, name="Vegetables", ordering=2, default_vat=19),
    ]


@pytest.yield_fixture
def container_types():
    yield [
        baker.make(
            "containers.container",
            size_class="Isolierbox",
            volume=6,
            deposit=Decimal("3.2"),
            standard=1,
            delivery_fee=Decimal("0.5"),
        ),
        baker.make(
            "containers.container",
            size_class="Greenbox",
            volume=4,
            deposit=Decimal("3.2"),
            standard=1,
            delivery_fee=Decimal("0.5"),
        ),
        baker.make(
            "containers.container",
            size_class="Yellowbox",
            volume=2,
            deposit=Decimal("3.2"),
            standard=1,
            delivery_fee=Decimal("0.5"),
        ),
    ]


@pytest.fixture
def product(traidoo_region):
    yield baker.make(
        "products.product",
        seller=baker.make(
            "users.user",
            first_name="Seller",
            is_cooperative_member=True,
            region=traidoo_region,
        ),
        price=1.1,
        amount=1,
        vat=19,
        container_type=baker.make("containers.container", deposit=3.2),
        region=traidoo_region,
    )


@pytest.fixture
def products(seller, traidoo_region, container_types, categories, delivery_options):
    yield [
        baker.make_recipe(
            "products.product",
            category=categories[0],
            seller=seller,
            price=10.6,
            amount=3,
            vat=19,
            region=traidoo_region,
            delivery_options=delivery_options,
            container_type=container_types[0],
            delivery_charge=0.1,
            unit="kg",
        ),
        baker.make_recipe(
            "products.product",
            category=categories[1],
            seller=seller,
            price=20.3,
            amount=1,
            vat=19,
            region=traidoo_region,
            delivery_options=delivery_options,
            container_type=container_types[0],
            delivery_charge=12,
            unit="kg",
        ),
    ]


@pytest.fixture
def products_items(products):
    yield [
        baker.make(Item, product=products[0], quantity=10),
        baker.make(Item, product=products[1], quantity=17),
    ]


@pytest.fixture
def delivery_options():
    yield [
        baker.make(DeliveryOption, name="traidoo", id=0),
        baker.make(DeliveryOption, name="seller", id=1),
        baker.make(DeliveryOption, name="buyer", id=2),
    ]


@pytest.fixture
def mangopay():
    with mock.patch(
        "payments.mixins.MangopayMixin.mangopay", new_callable=mock.PropertyMock
    ) as mangopay_mock:
        yield mangopay_mock


@pytest.fixture
def bucket():
    with mock.patch(
        "core.mixins.storage.StorageMixin.bucket", new_callable=mock.PropertyMock
    ) as bucket_mock:
        store_mock = mock.Mock()
        store_mock.configure_mock(name="document.pdf")
        bucket_mock.return_value.blob.return_value = store_mock
        yield bucket_mock


@pytest.fixture
def storage():
    with mock.patch(
        "google.cloud.storage.Client", new_callable=mock.PropertyMock
    ) as storage_mock:
        yield storage_mock


@pytest.fixture
def cart(buyer, products, delivery_options, delivery_address):
    products[0].delivery_charge = 1.1
    products[0].price = 60
    products[0].save()

    products[1].delivery_charge = 1.1
    products[1].price = 60
    products[1].save()

    cart = baker.make(
        "carts.cart",
        user=buyer,
        delivery_address=delivery_address,
        earliest_delivery_date=(
            datetime.datetime.now() + datetime.timedelta(days=2)
        ).date(),
    )

    baker.make(
        "carts.cartitem",
        product=products[0],
        cart=cart,
        quantity=1,
        delivery_option=delivery_options[0],
    )

    baker.make(
        "carts.cartitem",
        product=products[1],
        cart=cart,
        quantity=1,
        delivery_option=delivery_options[0],
    )

    yield cart


@pytest.fixture
def order(buyer, traidoo_region):
    yield baker.make(
        "orders.order",
        buyer=buyer,
        region=traidoo_region,
        earliest_delivery_date=timezone.make_aware(datetime.datetime.today()),
    )


@pytest.fixture
def delivery_address(buyer):
    yield baker.make(
        DeliveryAddress,
        company_name="ABC",
        street="Foo Street 1",
        zip="000",
        city="Munich",
        user=buyer,
    )


@pytest.fixture
def order_items(products, order, delivery_address, delivery_options):
    items = [
        baker.make(
            "orders.orderitem",
            product=products[0],
            quantity=3,
            order=order,
            delivery_address=delivery_address,
            delivery_option=delivery_options[0],
            latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
        ),
        baker.make(
            "orders.orderitem",
            product=products[1],
            quantity=2,
            order=order,
            delivery_address=delivery_address,
            delivery_option=delivery_options[1],
            latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
        ),
    ]

    yield items


@pytest.fixture
def order_confirmation(order, platform_user, logistics_user, traidoo_region):
    document = factories.OrderConfirmationBuyerFactory(
        order, region=traidoo_region
    ).compose()
    document.mangopay_payin_id = "payin-1"
    document.save()

    order.total_price = document.price_gross
    order.save()
    order.recalculate_items_delivery_fee()
    yield document


@pytest.fixture
def logistics_invoice(order, logistics_user, traidoo_region):
    invoice = factories.LogisticsInvoiceFactory(order, region=traidoo_region).compose()
    invoice.save()
    yield invoice


@pytest.fixture
def platform_invoice(
    order, seller, logistics_user, central_platform_user, traidoo_region
):
    invoice = factories.PlatformInvoiceFactory(
        order, seller=seller, region=traidoo_region
    ).compose()
    invoice.save()
    yield invoice


@pytest.fixture
def buyer_platform_invoice(order, seller, buyer, traidoo_region):
    buyer.is_cooperative_member = False
    invoice = factories.BuyerPlatformInvoiceFactory(
        order, seller=seller, region=traidoo_region
    ).compose()
    invoice.save()
    yield invoice


@pytest.fixture
def credit_note(order, platform_user, central_platform_user, traidoo_region):
    note = factories.CreditNoteFactory(order, region=traidoo_region).compose()
    note.save()
    yield note


@pytest.fixture
def producer_invoice(order, seller, logistics_user, order_items):
    invoice = factories.ProducerInvoiceFactory(
        order, seller=seller, region=traidoo_region
    ).compose()
    invoice.save()
    yield invoice


@pytest.fixture
def image_file():
    image_file = BytesIO()
    image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
    image.save(image_file, "png")
    image_file.name = "test.png"
    image_file.url = "http://foo.com/test.png"
    image_file.seek(0)
    yield image_file


@pytest.fixture
def cloud_storage_save():
    with mock.patch("storages.backends.gcloud.GoogleCloudStorage._save") as save:
        save.return_value = "test.png"
        yield save


@pytest.fixture
def cloud_storage_url():
    with mock.patch("storages.backends.gcloud.GoogleCloudStorage.url") as url:
        url.return_value = "http://test.png"
        yield url


@pytest.fixture
def other_region_product(neighbour_region, delivery_options):
    neighbour_seller = baker.make_recipe("users.user", region=neighbour_region)
    product = baker.make_recipe(
        "products.product",
        price=100,
        amount=3,
        vat=19,
        container_type=baker.make("containers.container", deposit=0.3),
        region=neighbour_region,
        seller=neighbour_seller,
        delivery_options=delivery_options,
    )
    baker.make(Item, product=product, quantity=100)

    yield product


@pytest.fixture
def order_with_neighbour_product(
    neighbour_region, delivery_address, order, order_items, other_region_product
):
    baker.make(
        "orders.orderitem",
        product=other_region_product,
        quantity=3,
        order=order,
        delivery_address=delivery_address,
        delivery_option_id=DeliveryOption.CENTRAL_LOGISTICS,
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
    )
    yield order


@pytest.fixture(autouse=True, scope="session")
def service_account():
    with mock.patch("google.oauth2.service_account") as service_account:
        service_account.return_value = mock.MagicMock()
        yield service_account


@pytest.fixture(autouse=True, scope="session")
def baker_support_for_better_array_field():
    baker.generators.add(
        "django_better_admin_arrayfield.models.fields.ArrayField", random_gen.gen_array
    )
    yield
