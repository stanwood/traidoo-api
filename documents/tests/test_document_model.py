import codecs
import datetime
import itertools
from decimal import Decimal

import pytz
import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time

from documents import factories
from documents.models import Document

pytestmark = pytest.mark.django_db


@pytest.fixture
def document_factories(order, traidoo_region, seller, order_items):
    yield (
        (
            factories.OrderConfirmationBuyerFactory,
            {"order": order, "region": traidoo_region},
        ),
        (factories.LogisticsInvoiceFactory, {"order": order, "region": traidoo_region}),
        (
            factories.PlatformInvoiceFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
        (
            factories.DeliveryOverviewBuyerFactory,
            {"order": order, "region": traidoo_region},
        ),
        (
            factories.ProducerInvoiceFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
        (
            factories.DeliveryOverviewSellerFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
        (
            factories.CreditNoteFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
    )


def test_total_price():
    document = Document()
    document.lines = [
        {"amount": 3, "price": 10, "vat_rate": 20, "count": 2, "seller_user_id": 1}
    ]

    assert document.price == 3 * 10 * 2
    assert document.price_gross == 3 * 10 * 2 * 1.20


def test_templates_syntax(document_factories):
    for factory, arguments in document_factories:
        factory(**arguments).compose().render_html()


def test_payment_reference_included_in_invoice(
    order, order_items, seller, logistics_user, traidoo_region
):
    document_factories = (
        (
            factories.ProducerInvoiceFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
        (factories.LogisticsInvoiceFactory, {"order": order, "region": traidoo_region}),
        (
            factories.PlatformInvoiceFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
    )
    for factory, arguments in document_factories:
        document = factory(**arguments).compose()
        document.payment_reference = "foo-reference"
        document.seller[
            "iban"
        ] = "foo-iban"  # this is how we are updating iban info in documents task
        assert "Reference: foo-reference" in document.render_html()


@freeze_time("2017-09-21 9:00")
def test_delivery_date_included_in_delivery_overview_documents(
    order, order_items, seller, logistics_user, traidoo_region
):
    settings.FEATURES["delivery_date"] = True

    order.earliest_delivery_date = timezone.make_aware(
        datetime.datetime.today(), pytz.timezone("CET")
    )
    order.created_at = timezone.make_aware(
        datetime.datetime.today(), pytz.timezone("CET")
    )
    order.save()
    order.recalculate_items_delivery_fee()

    document_factories = (
        (
            factories.DeliveryOverviewBuyerFactory,
            {"order": order, "region": traidoo_region},
        ),
        (
            factories.DeliveryOverviewSellerFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
    )
    for document_factory, arguments in document_factories:
        document = document_factory(**arguments).compose()
        html = BeautifulSoup(document.render_html(), features="html.parser")
        # both products have same delivery date
        assert len(html.findAll("strong", text="22.09.2017")) == 2


@freeze_time("2017-09-21 9:00")
def test_do_not_include_delivery_date_when_feature_is_disabled(
    order, order_items, seller, logistics_user, traidoo_region
):
    settings.FEATURES["delivery_date"] = False

    order.earliest_delivery_date = timezone.make_aware(
        datetime.datetime.today(), pytz.timezone("CET")
    )
    order.created_at = timezone.make_aware(
        datetime.datetime.today(), pytz.timezone("CET")
    )
    order.save()
    order.recalculate_items_delivery_fee()

    document_factories = (
        (
            factories.DeliveryOverviewBuyerFactory,
            {"order": order, "region": traidoo_region},
        ),
        (
            factories.DeliveryOverviewSellerFactory,
            {"order": order, "region": traidoo_region, "seller": seller},
        ),
    )
    for document_factory, arguments in document_factories:
        document = document_factory(**arguments).compose()
        html = BeautifulSoup(document.render_html(), features="html.parser")
        # both products have same delivery date
        assert len(html.findAll("th", text="Lieferdatum")) == 0
        assert len(html.findAll("strong", text="22.09.2017")) == 0


def test_seller_email_added_to_deliveryOverview_seller(
    order, order_items, seller, logistics_user, traidoo_region
):
    document = factories.DeliveryOverviewSellerFactory(
        order=order, region=traidoo_region, seller=seller
    ).compose()
    assert document.buyer["email"] == seller.email


def test_include_deposit_cost_in_order_confirmation_buyer(
    products,
    container_types,
    order_items,
    order,
    seller,
    logistics_user,
    platform_user,
    traidoo_region,
):
    products[1].container_type = container_types[1]
    products[1].save()

    order_items[1].product_snapshot = order_items[1].product.create_snapshot()
    order_items[1].save()

    document = factories.OrderConfirmationBuyerFactory(
        order=order, region=traidoo_region
    ).compose()

    html = BeautifulSoup(document.render_html(), features="html.parser")
    table = html.find("table")
    deposit_rows = table.find("td", text="Pfand").parent.find_next_siblings()[:2]
    deposit_lines = set()

    for row in deposit_rows:
        cells = row.find_all("td")
        deposit_lines.add(
            (
                cells[1].strong.text,  # container name
                cells[5].text.strip(),  # deposit
                cells[4].text.split("x")[0].strip(),  # count
                cells[6].text,  # total price,
                cells[3].text,  # vat rate
            )
        )

    assert deposit_lines == {
        ("Greenbox", "€ 3,20 / Stück", "2", "€ 6,40", "19,00%"),
        ("Isolierbox", "€ 3,20 / Stück", "3", "€ 9,60", "19,00%"),
    }

    deposits_total = html.find("div", text="Summe Pfand Netto").find_next_sibling().text
    assert deposits_total == "€ 16,00"

    price_total = html.find("div", text="Gesamt (Brutto)").find_next_sibling().text
    assert price_total == "€ 180,88"  # deposit cost should be included in total


def test_added_deposit_costs(
    order, order_items, seller, logistics_user, traidoo_region
):
    html = (
        factories.ProducerInvoiceFactory(
            order=order, region=traidoo_region, seller=seller
        )
        .compose()
        .render_html()
    )

    with codecs.open("producer_invoice.html", "w", encoding="utf-8") as out_file:
        out_file.write(html)

    html = BeautifulSoup(html, features="html.parser")
    table = html.find("table")

    table.prettify()
    row = table.find("td", text="Pfand").parent.find_next_siblings()[0]
    cells = row.find_all("td")
    deposit_line = (
        cells[1].strong.text,  # container name
        cells[5].text.strip(),  # deposit
        cells[4].text.split("x")[0].strip(),  # count
        cells[6].text,  # total price,
        cells[3].text,  # vat rate
    )
    assert deposit_line == (
        "Isolierbox",
        "\u20ac 3,20 / Stück",
        "5",
        "\u20ac 16,00",
        "19,00%",
    )

    deposits_total = html.find("div", text="Summe Pfand Netto").find_next_sibling().text
    assert deposits_total == "€ 16,00"

    price_total = (
        html.find("strong", text="Endsumme").parent.find_next_sibling().text.strip()
    )
    assert price_total == "€ 180,88"  # deposit cost should be included in total


def test_add_delivery_fee_if_producer_delivers_items(
    order, order_items, seller, logistics_user, traidoo_region
):
    order.recalculate_items_delivery_fee()

    html = (
        factories.ProducerInvoiceFactory(
            order=order, region=traidoo_region, seller=seller
        )
        .compose()
        .render_html()
    )
    assert "Lieferung von" in html


def test_vat_amount_added_to_invoice_sum(
    order, order_items, seller, logistics_user, traidoo_region
):
    document = factories.ProducerInvoiceFactory(
        order=order, region=traidoo_region, seller=seller
    ).compose()
    html = document.render_html()
    html = BeautifulSoup(html, features="html.parser")
    vat_amount_cells = html.find_all(attrs={"class": "sum-vat-amount"})
    # TODO: do not use static values, calculate vat
    assert "28,88" in vat_amount_cells[0].text


def test_gross_rounding():

    document = Document(
        lines=[
            {"price": 41, "count": 1, "amount": 1, "vat_rate": 7, "seller_user_id": 1},
            {"price": 7.9, "count": 1, "amount": 1, "vat_rate": 7, "seller_user_id": 2},
            {
                "price": 4.89,
                "count": 1,
                "amount": 1,
                "vat_rate": 19,
                "seller_user_id": 3,
            },
            {
                "price": 4.89,
                "count": 1,
                "amount": 1,
                "vat_rate": 19,
                "seller_user_id": 4,
            },
        ]
    )

    assert document.price_gross_cents == 6396

    document = Document(
        lines=[
            {
                "price": 7.80,
                "count": 1,
                "amount": 1,
                "vat_rate": 7,
                "seller_user_id": 4,
            },
            {
                "price": 0.97,
                "count": 1,
                "amount": 1,
                "vat_rate": 7,
                "seller_user_id": 4,
            },
        ]
    )

    assert document.price_gross_cents == 938


def test_euro_to_cents_conversion():

    document = Document(
        lines=[
            {
                "price": 18.17,
                "count": 1,
                "amount": 1,
                "vat_rate": 10,
                "seller_user_id": 1,
            }
        ]
    )

    assert document.price_gross_cents == 1999


def test_total_error():

    null = None
    lines = [
        {
            "name": "Roggenbrötchen Bio",
            "unit": "Stück",
            "count": 1.0,
            "price": 0.34,
            "amount": 5.0,
            "number": "5184813602439168",
            "category": "Produkte",
            "producer": "Traidoo",
            "vat_rate": 7.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": "DE-ÖKO-006",
        },
        {
            "name": "Schlackwurst vom Schwein Bio",
            "unit": "kg",
            "count": 1.0,
            "price": 15.5,
            "amount": 0.9,
            "number": "5133692074721280",
            "category": "Produkte",
            "producer": "Traidoo",
            "vat_rate": 7.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": "DE-ÖKO-006",
        },
        {
            "name": "Vollkornbrötchen bemehlt Bio",
            "unit": "Stück",
            "count": 1.0,
            "price": 0.34,
            "amount": 5.0,
            "number": "4816629141602304",
            "category": "Produkte",
            "producer": "Traidoo",
            "vat_rate": 7.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": "DE-ÖKO-006",
        },
        {
            "name": "Vollkornbrötchen mit Mohn Bio",
            "unit": "Stück",
            "count": 1.0,
            "price": 0.34,
            "amount": 5.0,
            "number": "6331673855655936",
            "category": "Produkte",
            "producer": "Traidoo",
            "vat_rate": 7.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": "DE-ÖKO-006",
        },
        {
            "name": "Vollkornbrötchen mit Sesam Bio",
            "unit": "Stück",
            "count": 1.0,
            "price": 0.34,
            "amount": 5.0,
            "number": "5623015794540544",
            "category": "Produkte",
            "producer": "Traidoo",
            "vat_rate": 7.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": "DE-ÖKO-006",
        },
        {
            "name": "Eigene Verpackung  wie Napf 5",
            "unit": "Stk",
            "count": 1.0,
            "price": 0.0,
            "amount": 1.0,
            "number": "5194211779411968",
            "category": "Pfand",
            "producer": "",
            "vat_rate": 19.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": null,
        },
        {
            "name": "Eigene Verpackung wie Napf 0.5",
            "unit": "Stk",
            "count": 1.0,
            "price": 0.0,
            "amount": 1.0,
            "number": "6227976249147392",
            "category": "Pfand",
            "producer": "",
            "vat_rate": 19.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": null,
        },
        {
            "name": "Eigene Verpackung wie Napf 0.5",
            "unit": "Stk",
            "count": 1.0,
            "price": 0.0,
            "amount": 1.0,
            "number": "6227976249147392",
            "category": "Pfand",
            "producer": "",
            "vat_rate": 19.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": null,
        },
        {
            "name": "Eigene Verpackung wie Napf 0.5",
            "unit": "Stk",
            "count": 1.0,
            "price": 0.0,
            "amount": 1.0,
            "number": "6227976249147392",
            "category": "Pfand",
            "producer": "",
            "vat_rate": 19.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": null,
        },
        {
            "name": "Eigene Verpackung wie Napf 0.5",
            "unit": "Stk",
            "count": 1.0,
            "price": 0.0,
            "amount": 1.0,
            "number": "6227976249147392",
            "category": "Pfand",
            "producer": "",
            "vat_rate": 19.0,
            "delivery_date": null,
            "container_name": null,
            "seller_user_id": 4891776154337280,
            "delivery_company": null,
            "organic_control_body": null,
        },
    ]

    document = Document(lines=lines)

    assert document.price_gross_cents == 2220
    assert document.price_gross == 22.2


def test_include_deposit_cost_in_order_confirmation_buyer_and_merge_containers(
    order,
    order_items,
    platform_user,
    logistics_user,
    products,
    container_types,
    traidoo_region,
):
    document = factories.OrderConfirmationBuyerFactory(
        order=order, region=traidoo_region
    ).compose()

    html = BeautifulSoup(document.render_html(), features="html.parser")
    table = html.find("table")
    deposit_rows = table.find("td", text="Pfand").parent.find_next_siblings()[:1]
    deposit_lines = set()

    for row in deposit_rows:
        cells = row.find_all("td")
        deposit_lines.add(
            (
                cells[1].strong.text,  # container name
                cells[5].text.strip(),  # deposit
                cells[4].text.split("x")[0].strip(),  # count
                cells[6].text,  # total price,
                cells[3].text,  # vat rate
            )
        )

    assert deposit_lines == {("Isolierbox", "€ 3,20 / Stück", "5", "€ 16,00", "19,00%")}

    deposits_total = html.find("div", text="Summe Pfand Netto").find_next_sibling().text
    assert deposits_total == "€ 16,00"

    price_total = html.find("div", text="Gesamt (Brutto)").find_next_sibling().text
    assert price_total == "€ 180,88"  # deposit cost should be included in total


def test_delivery_address_included_in_delivery_documents(
    order, order_items, traidoo_region, seller, logistics_user, traidoo_settings
):
    html = (
        factories.DeliveryOverviewSellerFactory(order, traidoo_region, seller=seller)
        .compose()
        .render_html()
    )
    html = BeautifulSoup(html, features="html.parser")
    assert len(html.find_all("p", text=lambda text: "von Best apples" in text)) == 2
    assert len(html.find_all("p", text=lambda text: "nach ABC" in text)) == 2


def test_document_receivers_emails(
    document_factories,
    buyer,
    platform_user,
    logistics_user,
    seller,
    central_platform_user,
):

    document_type_receivers_mapping = {
        Document.TYPES.get_value("buyer_platform_invoice"): {
            buyer.email,
            platform_user.email,
        },
        Document.TYPES.get_value("platform_invoice"): {
            seller.email,
            central_platform_user.email,
        },
        Document.TYPES.get_value("logistics_invoice"): {
            buyer.email,
            logistics_user.email,
        },
        Document.TYPES.get_value("producer_invoice"): {buyer.email, seller.email},
        Document.TYPES.get_value("order_confirmation_buyer"): {
            buyer.email,
            platform_user.email,
        },
        Document.TYPES.get_value("delivery_overview_buyer"): {
            buyer.email,
            logistics_user.email,
        },
        Document.TYPES.get_value("delivery_overview_seller"): {
            seller.email,
            logistics_user.email,
        },
        Document.TYPES.get_value("receipt_buyer"): {seller.email, platform_user.email},
        Document.TYPES.get_value("credit_note"): {
            platform_user.email,
            central_platform_user.email,
        },
    }

    for factory, arguments in document_factories:
        document = factory(**arguments).compose()
        assert (
            set(document.receivers_emails)
            == document_type_receivers_mapping[document.document_type]
        ), f"{document.document_type} wrong distribution list"


def test_send_delivery_documents_to_both_logistics_companies_for_cross_border_orders(
    order_with_neighbour_product, other_region_product, traidoo_region, neighbour_region
):

    seller_delivery_document = factories.DeliveryOverviewSellerFactory(
        order=order_with_neighbour_product,
        region=other_region_product.region,
        seller=other_region_product.seller,
    ).compose()

    assert set(seller_delivery_document.receivers_emails) == {
        traidoo_region.setting.logistics_company.email,
        neighbour_region.setting.logistics_company.email,
        other_region_product.seller.email,
    }


@pytest.mark.parametrize(
    argnames="document_type,file_pattern",
    argvalues=(
        (
            "buyer_platform_invoice",
            "{order_id}-{document_id}-invoice_platform_{buyer[company_name]}.pdf",
        ),
        (
            "platform_invoice",
            "{order_id}-{document_id}-invoice_platform_producer_{buyer[company_name]}.pdf",
        ),
        (
            "logistics_invoice",
            "{order_id}-{document_id}-invoice_logistics_{seller[company_name]}.pdf",
        ),
        (
            "producer_invoice",
            "{order_id}-{document_id}-invoice_producer_{seller[company_name]}.pdf",
        ),
        (
            "order_confirmation_buyer",
            "{order_id}-{document_id}-order_confirmation_buyer.pdf",
        ),
        (
            "delivery_overview_buyer",
            "{order_id}-{document_id}-delivery_overview_buyer.pdf",
        ),
        (
            "delivery_overview_seller",
            "{order_id}-{document_id}-producer_delivery_note_{buyer[company_name]}.pdf",
        ),
        ("receipt_buyer", "{order_id}-{document_id}-buyer_payment_receipt.pdf"),
        ("credit_note", "{order_id}-{document_id}-credit_note.pdf"),
    ),
)
def test_document_pdf_file_names(order, document_type, file_pattern):
    seller = {"company_name": "Seller Ltd"}
    buyer = {"company_name": "Buyer Ltd"}
    document = Document(
        document_type=Document.TYPES.get_value(document_type),
        order=order,
        seller=seller,
        buyer=buyer,
    )
    document.save()
    assert document.pdf_file_name == file_pattern.format(
        order_id=order.id, document_id=document.id, seller=seller, buyer=buyer
    )
