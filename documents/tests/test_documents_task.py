import itertools
from decimal import Decimal
from unittest import mock

import pytest
from anymail.exceptions import AnymailError
from django.urls import reverse
from django.test import override_settings
from model_bakery import baker

from documents.models import Document, DocumentSendLog
from Traidoo import errors

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def banking_alias():
    with mock.patch(
        "payments.mixins.MangopayMixin.get_wallet_banking_alias"
    ) as get_wallet_banking_alias:
        get_wallet_banking_alias.return_value = {
            "iban": "FR7618829754160173622224251",
            "bic": "CMBRFR2BCME",
            "id": "234514543",
            "owner_name": "Test Test",
        }
        yield get_wallet_banking_alias


@pytest.fixture(autouse=True)
def user_wallet():
    with mock.patch("payments.mixins.MangopayMixin.get_user_wallet") as get_user_wallet:
        get_user_wallet.return_value = {
            "Id": "wallet-1",
            "Currency": "EUR",
            "Description": "Default",
        }
        yield get_user_wallet


@pytest.fixture(autouse=True)
def render_pdf():
    with mock.patch("documents.models.Document.render_pdf") as render:
        render.return_value = "PDF"
        yield render


@pytest.fixture(autouse=True)
def bucket(bucket):
    bucket.return_value.blob.return_value.download_as_string.return_value = "data"
    bucket.return_value.blob.return_value.content_type = "text/plain"
    yield bucket


def test_documents_stored_in_storage(bucket, client, order, order_items, buyer):
    buyer.is_cooperative_member = False
    buyer.save()
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    documents = Document.objects.filter(order=order)

    assert documents.count() == 8

    blob = bucket.return_value.blob
    for document in documents:
        blob.assert_any_call(f"documents/{order.id}/{document.pdf_file_name}".encode())

    upload_from_string = blob.return_value.upload_from_string
    assert upload_from_string.call_count == 8
    upload_from_string.assert_called_with("PDF", "application/pdf")


def test_do_not_duplicate_documents(bucket, client, order, order_items, buyer):
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))
    documents = Document.objects.filter(order=order)
    assert documents.count() == 7


@override_settings(FEATURES={"routes": True})
def test_documents_stored_in_storage_with_third_party_delivery(
    bucket,
    products,
    delivery_options,
    order,
    order_items,
    client,
    buyer,
    traidoo_region,
):
    buyer.is_cooperative_member = False
    buyer.save()

    products[0].third_party_delivery = True
    products[0].save()

    order_items[0].delivery_option = delivery_options[1]
    order_items[0].save()

    order.recalculate_items_delivery_fee()
    order_items[0].refresh_from_db()

    user = baker.make_recipe("users.user", region=traidoo_region)
    baker.make("jobs.Job", user=user, order_item=order_items[0])

    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    documents = Document.objects.filter(order=order)
    assert documents.count() == 8
    blob = bucket.return_value.blob
    for document in documents:
        blob.assert_any_call(f"documents/{order.id}/{document.pdf_file_name}".encode())

    upload_from_string = blob.return_value.upload_from_string
    assert upload_from_string.call_count == 8
    upload_from_string.assert_called_with("PDF", "application/pdf")


def test_do_not_render_credit_note_when_local_platform_not_defined(
    order, order_items, client, traidoo_settings
):

    traidoo_settings.platform_user = None
    traidoo_settings.save()
    response = client.post(
        reverse("task", kwargs={"order_id": order.id, "document_set": "all"})
    )
    assert response.status_code == 200
    assert (
        Document.objects.filter(
            document_type=Document.TYPES.get_value("credit_note"), order_id=order.id
        ).count()
        == 0
    )


def test_do_not_render_credit_note_when_local_share_not_defined(
    order, order_items, client, traidoo_settings
):

    traidoo_settings.central_share = None
    traidoo_settings.save()
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))
    assert (
        Document.objects.filter(
            document_type=Document.TYPES.get_value("credit_note"), order_id=order.id
        ).count()
        == 0
    )


def test_do_not_render_credit_note_when_central_logistics_not_set(
    order, order_items, client, traidoo_settings
):

    traidoo_settings.enable_platform_fee_share = False
    traidoo_settings.save()
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))
    assert (
        Document.objects.filter(
            document_type=Document.TYPES.get_value("credit_note"), order_id=order.id
        ).count()
        == 0
    )


def test_do_not_render_credit_note_when_local_platform_share_zero(
    order, order_items, client, traidoo_settings
):
    traidoo_settings.central_share = Decimal("100")
    traidoo_settings.save()
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))
    assert (
        Document.objects.filter(
            document_type=Document.TYPES.get_value("credit_note"), order_id=order.id
        ).count()
        == 0
    )


def test_documents_sent_to_email(
    mailoutbox,
    client,
    order,
    order_items,
    buyer,
    seller,
    central_platform_user,
    platform_user,
    logistics_user,
):
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    assert len(mailoutbox) == 5

    unique_list_of_receivers = set(itertools.chain(*[mail.to for mail in mailoutbox]))

    assert unique_list_of_receivers == {
        buyer.email,
        seller.email,
        central_platform_user.email,
        platform_user.email,
        logistics_user.email,
    }


def test_documents_sent_to_all_user_emails(
    mailoutbox,
    buyer,
    seller,
    client,
    order,
    order_items,
    central_platform_user,
    platform_user,
    logistics_user,
):
    buyer.invoice_email = "second-buyer@example.com"
    buyer.save()
    seller.invoice_email = "second-seller@example.com"
    seller.save()

    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    assert len(mailoutbox) == 7

    all_receivers_emails = set(itertools.chain(*[mail.to for mail in mailoutbox]))
    assert all_receivers_emails == {
        buyer.email,
        buyer.invoice_email,
        seller.email,
        seller.invoice_email,
        central_platform_user.email,
        platform_user.email,
        logistics_user.email,
    }


def test_track_sending_emails(
    mailoutbox,
    buyer,
    seller,
    client,
    order,
    order_items,
    central_platform_user,
    platform_user,
    logistics_user,
):
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    for mail in mailoutbox:
        assert DocumentSendLog.objects.get(email=mail.to[0])


def test_do_not_resend_documents_at_rerun(
    mailoutbox,
    buyer,
    seller,
    client,
    order,
    order_items,
    central_platform_user,
    platform_user,
    logistics_user,
):
    DocumentSendLog.objects.create(email=buyer.email, order=order)
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))
    all_receivers_emails = set(itertools.chain(*[mail.to for mail in mailoutbox]))
    assert buyer.email not in all_receivers_emails


@mock.patch("documents.tasks.documents.send_mail")
def test_keep_email_send_log_after_exception(
    send_mail,
    buyer,
    seller,
    client,
    order,
    order_items,
    central_platform_user,
    platform_user,
    logistics_user,
):

    send_mail.side_effect = [True, True, AnymailError("Boom")]
    with pytest.raises(AnymailError):
        client.post(
            reverse("task", kwargs={"order_id": order.id, "document_set": "all"})
        )
    assert DocumentSendLog.objects.count() == 2


def test_use_mangopay_iban_alias_in_order_confirmation(client, order, order_items):
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    order_confirmation = Document.objects.get(document_type="Order Confirmation Buyer")
    assert order_confirmation.seller["iban"] == "FR7618829754160173622224251"
    assert order_confirmation.seller["bic"] == "CMBRFR2BCME"
    assert order_confirmation.bank_account_owner == "Test Test"

    invoices = Document.objects.filter(document_type__contains="Invoice")

    for invoice in invoices:
        assert invoice.seller["iban"] == (
            "Bitte nutzen Sie die Kontodaten in der Bestellzusammenfassung "
            "zur Zahlung aller Rechnungen dieser Bestellung."
        )
        assert not invoice.seller["bic"]


def test_fail_tasks_when_buyer_does_not_have_mangopay_account(order, client):
    previous_user_id = order.buyer.mangopay_user_id
    order.buyer.mangopay_user_id = None
    order.buyer.save()

    with pytest.raises(errors.PaymentError):
        client.post(
            reverse("task", kwargs={"order_id": order.id, "document_set": "all"})
        )

    order.buyer.mangopay_user_id = previous_user_id
    order.buyer.save()


def test_hide_logistics_iban_in_delivery_documents(client, order, order_items):
    client.post(reverse("task", kwargs={"order_id": order.id, "document_set": "all"}))

    for document in Document.objects.filter(document_type__contains="Delivery"):
        assert document.seller["iban"] is None


def test_create_logistics_invoice_for_neighbouring_logistic_company(
    client, order_with_neighbour_product, traidoo_region, neighbour_region
):
    client.post(
        reverse(
            "task",
            kwargs={"order_id": order_with_neighbour_product.id, "document_set": "all"},
        )
    )
    logistic_invoices = Document.objects.filter(
        order=order_with_neighbour_product,
        document_type=Document.TYPES.get_value("logistics_invoice"),
    )

    assert logistic_invoices.count() == 2

    assert set(invoice.seller["company_name"] for invoice in logistic_invoices) == {
        traidoo_region.setting.logistics_company.company_name,
        neighbour_region.setting.logistics_company.company_name,
    }


def test_send_delivery_documents_to_both_logistics_companies_for_cross_region_orders(
    order_with_neighbour_product, buyer, other_region_product, client, mailoutbox
):

    logistics_company_from_producer_region = (
        other_region_product.region.setting.logistics_company
    )
    logistics_company_of_buyer = (
        order_with_neighbour_product.region.setting.logistics_company
    )

    client.post(
        reverse(
            "task",
            kwargs={"order_id": order_with_neighbour_product.id, "document_set": "all"},
        )
    )

    mail_receivers = set(itertools.chain(*[mail.to for mail in mailoutbox]))
    # these are not specific enough assertions since other docs like invoices might
    # have been sent to these mails
    assert logistics_company_from_producer_region.email in mail_receivers
    assert logistics_company_of_buyer.email in mail_receivers


def test_create_buyer_delivery_overview_only_for_buyer_logistics_company(
    order_with_neighbour_product, client
):
    client.post(
        reverse(
            "task",
            kwargs={"order_id": order_with_neighbour_product.id, "document_set": "all"},
        )
    )

    delivery_documents = Document.objects.filter(
        document_type=Document.TYPES.get_value("delivery_overview_buyer")
    )
    assert delivery_documents.count() == 1
    document = delivery_documents.first()

    assert (
        document.seller["email"]
        == order_with_neighbour_product.region.setting.logistics_company.email
    )
