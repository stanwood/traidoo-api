import datetime

import pytest
from bs4 import BeautifulSoup
from django.utils import timezone
from model_mommy import mommy

from delivery_options.models import DeliveryOption
from documents import factories
from orders.models import Order, OrderItem, User

pytestmark = pytest.mark.django_db


def test_create_local_admin_credit_note(
    order, order_items, seller, platform_user, traidoo_region
):
    credit_note = factories.CreditNoteFactory(order, traidoo_region, seller).compose()
    credit_note.save()

    assert (
        credit_note.lines[0]["price"] == order.local_platform_owner_platform_fee.netto
    )
    assert credit_note.buyer == factories.CreditNoteFactory.as_dict(
        traidoo_region.setting.platform_user
    )
    assert credit_note.seller == factories.CreditNoteFactory.as_dict(
        User.central_platform_user()
    )
    assert len(credit_note.lines) == 1


def test_third_party_logistic_invoice(
    send_task,
    order,
    platform_user,
    traidoo_region,
    delivery_address,
    delivery_options,
    logistics_user,
    traidoo_settings,
    order_items,
    buyer,
    products,
):
    order.recalculate_items_delivery_fee()
    products[0].third_party_delivery = True
    products[0].save()
    order_items[0].delivery_option_id = DeliveryOption.SELLER
    order_items[0].save()

    user = mommy.make_recipe("users.user", region=traidoo_region)
    mommy.make("jobs.Job", user=user, order_item=order_items[0])

    order.recalculate_items_delivery_fee()

    factory = factories.ThirdPartyLogisticsInvoiceFactory(order, region=traidoo_region)

    documents = list(factory.compose())
    assert len(documents) == 1
    documents[0].save()
    document = documents[0]

    assert document.seller == factories.ThirdPartyLogisticsInvoiceFactory.as_dict(user)
    assert document.buyer == factories.ThirdPartyLogisticsInvoiceFactory.as_company(
        buyer
    )

    assert document.order_id == order.id
    assert len(document.lines) == 1
    order_items[0].refresh_from_db()
    assert document.lines[0] == {
        "amount": 1.0,
        "count": 1.0,
        "name": f"Lieferung von {order_items[0].product.name}",
        "number": order_items[0].product_id,
        "price": float(order_items[0].delivery_fee),
        "producer": user.company_name,
        "seller_user_id": user.id,
        "unit": "",
        "vat_rate": traidoo_settings.mc_swiss_delivery_fee_vat,
        "category": "",
    }


def test_producer_invoice(
    order,
    order_items,
    traidoo_region,
    container_types,
    delivery_address,
    delivery_options,
    logistics_user,
    seller,
    buyer,
    products,
):
    other_seller = mommy.make_recipe("users.user")
    products[1].seller = other_seller
    products[1].save()

    factory = factories.ProducerInvoiceFactory(
        order, seller=seller, region=traidoo_region
    )
    document = factory.compose()
    document.save()

    assert document.seller == factories.ProducerInvoiceFactory.as_dict(seller)
    assert document.buyer == factories.ProducerInvoiceFactory.as_company(buyer)

    assert len(document.lines) == 2
    assert document.order_id == order.id
    assert document.lines[0] == {
        "amount": 3.0,
        "category": "Produkte",
        "count": 3.0,
        "name": products[0].name,
        "number": products[0].id,
        "organic_control_body": seller.organic_control_body,
        "price": 10.6,
        "producer": seller.company_name,
        "seller_user_id": seller.id,
        "unit": products[0].unit,
        "vat_rate": products[0].vat,
    }
    assert document.lines[1] == {
        "amount": 1,
        "category": "Pfand",
        "count": 3.0,
        "name": "Isolierbox",
        "number": container_types[0].id,
        "price": 3.2,
        "producer": "",
        "seller_user_id": seller.id,
        "unit": "Stück",
        "vat_rate": 19.0,
    }


def test_merge_same_products(
    buyer,
    traidoo_region,
    products,
    delivery_address,
    delivery_options,
    seller,
    logistics_user,
):
    order = Order(buyer=buyer, region=traidoo_region)
    order.save()
    order.recalculate_items_delivery_fee()

    order_items = [
        OrderItem(
            product=products[0],
            quantity=5,
            order=order,
            delivery_address=delivery_address,
            delivery_option=delivery_options[0],
            latest_delivery_date=(timezone.now().date() + datetime.timedelta(days=3)),
        ),
        OrderItem(
            product=products[0],
            quantity=5,
            order=order,
            delivery_address=delivery_address,
            delivery_option=delivery_options[0],
            latest_delivery_date=(timezone.now().date() + datetime.timedelta(days=2)),
        ),
        OrderItem(
            product=products[0],
            quantity=5,
            order=order,
            delivery_address=delivery_address,
            delivery_option=delivery_options[0],
            latest_delivery_date=(timezone.now().date() + datetime.timedelta(days=1)),
        ),
    ]

    [items.save() for items in order_items]
    order.recalculate_items_delivery_fee()

    factory = factories.ProducerInvoiceFactory(
        order=order, seller=seller, region=traidoo_region
    )

    assert len(factory._items) == 1
    assert factory._items[0].product == products[0]
    assert factory._items[0].quantity == 15
    assert factory._items[0].product_snapshot == order_items[0].product_snapshot
    assert factory._items[0].order == order
    assert factory._items[0].delivery_address == order_items[0].delivery_address
    assert factory._items[0].delivery_option == order_items[0].delivery_option
    assert factory._items[0].latest_delivery_date == order_items[0].latest_delivery_date


def test_use_buyer_delivery_address_when_self_collect(
    seller,
    logistics_user,
    products,
    delivery_options,
    buyer,
    traidoo_region,
    traidoo_settings,
):

    order = mommy.make(
        Order,
        buyer=buyer,
        earliest_delivery_date=timezone.make_aware(datetime.datetime.today()),
        region=traidoo_region,
    )
    order.save()
    order_item = mommy.make(
        OrderItem,
        product=products[0],
        quantity=1,
        order=order,
        delivery_address=None,
        delivery_option=delivery_options[2],
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
    )
    order_item.save()

    delivery_documents_factories = [
        factories.DeliveryOverviewSellerFactory,
        factories.DeliveryOverviewBuyerFactory,
    ]

    for DeliveryDocumentFactory in delivery_documents_factories:
        html = (
            DeliveryDocumentFactory(order, traidoo_region, seller)
            .compose()
            .render_html()
        )
        html = BeautifulSoup(html, features="html.parser")
        assert len(html.find_all("p", text=lambda text: "von Best apples" in text)) == 1
        assert len(html.find_all("p", text=lambda text: "nach ACME" in text)) == 1
