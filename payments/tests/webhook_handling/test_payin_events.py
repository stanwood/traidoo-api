import datetime
from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from documents import factories
from mails.utils import get_admin_emails
from orders.models import Order, OrderItem
from payments.client.exceptions import MangopayError, MangopayTransferError

pytestmark = pytest.mark.django_db


@pytest.fixture
def mangopay_successful_payin_processing(
    mangopay,
    order,
    buyer,
    order_items,
    order_confirmation,
    logistics_invoice,
    producer_invoice,
    platform_invoice,
    credit_note,
    send_task,
    traidoo_region,
    central_platform_user,
    logistics_user,
):

    mangopay.return_value.get_banking_alias.return_value = {
        "OwnerName": "MANGOPAY",
        "IBAN": "LU93381JC55EN0X2NIFL",
        "BIC": "MPAYFRP1EMI",
        "CreditedUserId": "mangopay-buyer-1",
        "Country": "FR",
        "Tag": "a tag",
        "CreationDate": "1486402774",
        "Active": "",
        "Type": "IBAN",
        "Id": "buyer-banking-alias-1",
        "WalletId": "buyer-wallet-1",
    }

    mangopay.return_value.get_wallet.return_value = {
        "Currency": "EUR",
        "Id": "buyer-wallet-1",
        "Description": "Default",
        "Balance": {"Currency": "EUR", "Amount": 943191},
    }
    mangopay.return_value.get_user_wallets.side_effect = [
        [{"Id": "seller-1-wallet", "Currency": "EUR", "Description": "Default"}],
        [
            {
                "Id": "logistics-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
                "Owners": [logistics_user.mangopay_user_id],
            }
        ],
        [
            {
                "Id": "global-platform-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
                "Owners": [central_platform_user.mangopay_user_id],
            }
        ],
        [
            {
                "Id": "local-platform-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
            }
        ],
    ]

    mangopay.return_value.transfer.return_value = {"Status": "SUCCEEDED"}
    yield mangopay


@pytest.fixture
def mangopay_bank_alias_payin(mangopay_successful_payin_processing):
    mangopay_successful_payin_processing.return_value.get_pay_in.return_value = {
        "Status": "SUCCEEDED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR"},
        "DebitedFunds": {"Currency": "EUR", "Amount": 18088},
        "Fees": {"Currency": "EUR", "Amount": 593},
        "Id": "payin-1",
        "AuthorId": "mangopay-user-buyer",
        "BankingAliasId": "234514543",
    }

    yield mangopay_successful_payin_processing


@pytest.fixture
def mangopay_wire_reference_payin(mangopay_successful_payin_processing):
    mangopay_successful_payin_processing.return_value.get_pay_in.return_value = {
        "Status": "SUCCEEDED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR"},
        "DebitedFunds": {"Currency": "EUR", "Amount": 18088},
        "Fees": {"Currency": "EUR", "Amount": 593},
        "Id": "payin-1",
        "AuthorId": "mangopay-user-buyer",
    }

    yield mangopay_successful_payin_processing


def test_payin_for_order_confirmation_wrong_amount(
    mangopay, order_items, mailoutbox, order_confirmation, api_client, buyer
):
    # Only applies to bankwire pay in to wallet
    # TODO Remove once all pay ins are migrated to banking alias pay ins
    mangopay.return_value.get_pay_in.return_value = {
        "Status": "SUCCEEDED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR", "Amount": 713},
        "DebitedFunds": {"Currency": "EUR", "Amount": 713},
        "Fees": {"Currency": "EUR", "Amount": 0},
        "Id": "payin-1",
        "AuthorId": buyer.mangopay_user_id,
    }

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    assert (
        f"Wrong amount received in payin payin-1 for document {order_confirmation.id}"
        in mailoutbox[-1].body
    )
    assert "Expected (in cents) `18088`, but received `713`" in mailoutbox[-1].body


def test_transfer_related_document_not_found(
    mangopay_wire_reference_payin, mailoutbox, api_client
):
    # TODO Remove once all pay ins are migrated to banking alias pay ins
    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-fake-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    assert "Fehler bei der Verarbeitung der Zahlung" in mailoutbox[-1].subject
    assert "Document related to payin payin-fake-1 not found." in mailoutbox[-1].body


def test_transfers_after_successful_processing(
    mangopay_bank_alias_payin, api_client, order
):
    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    transfer = mangopay_bank_alias_payin.return_value.transfer

    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "seller-1-wallet",
        amount=178.98,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Producer Invoice Seller: Best apples Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "logistics-1-wallet",
        amount=18.81,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Logistics Invoice Seller: Traidoo Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "local-platform-1-wallet",
        amount=9.71,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Credit Note Seller: Traidoo Buyer: Traidoo",
    )

    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "global-platform-1-wallet",
        amount=5.39,
        fees=1.08,
        tag=f"v2 Order: {order.id} Document: Platform Invoice Seller: Traidoo Buyer: Best apples",
    )


def test_pay_oldest_order_first(
    mangopay_bank_alias_payin,
    order,
    api_client,
    order_confirmation,
    buyer,
    traidoo_region,
    products,
    delivery_address,
    delivery_options,
):

    new_order = baker.make(
        Order,
        buyer=buyer,
        region=traidoo_region,
        earliest_delivery_date=timezone.make_aware(datetime.datetime.today()),
    )

    product = products[0]
    product.amount = 10
    product.save()

    baker.make(
        OrderItem,
        product=product,
        quantity=1,
        order=new_order,
        delivery_address=delivery_address,
        delivery_option=delivery_options[0],
        latest_delivery_date=timezone.now().date() + datetime.timedelta(days=3),
    )

    factories.PlatformInvoiceFactory(
        new_order, traidoo_region, product.seller
    ).compose().save()
    new_order_confirmation = factories.OrderConfirmationBuyerFactory(
        new_order, traidoo_region
    ).compose()
    new_order_confirmation.save()
    new_order.total_price = new_order_confirmation.price_gross
    new_order.save()
    factories.ProducerInvoiceFactory(
        new_order, traidoo_region, product.seller
    ).compose().save()
    mangopay_bank_alias_payin.return_value.get_wallet.side_effect = [
        # first order check if we can afford to pay
        {
            "Currency": "EUR",
            "Id": "buyer-wallet-1",
            "Description": "Default",
            "Balance": {"Currency": "EUR", "Amount": 943191},
        },
        # second order
        {
            "Currency": "EUR",
            "Id": "buyer-wallet-1",
            "Description": "Default",
            "Balance": {"Currency": "EUR", "Amount": 0},
        },
        # final call to check if there's anything left in wallet
        {
            "Currency": "EUR",
            "Id": "buyer-wallet-1",
            "Description": "Default",
            "Balance": {"Currency": "EUR", "Amount": 0},
        },
    ]

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    order.refresh_from_db()
    assert order.is_paid
    assert not new_order.is_paid


def test_transfer_to_global_platform_owner_if_local_does_not_have_mangopay_account(
    mangopay_bank_alias_payin, api_client, order, platform_user, mailoutbox, admin
):
    platform_user.mangopay_user_id = None
    platform_user.save()

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    transfer = mangopay_bank_alias_payin.return_value.transfer

    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "seller-1-wallet",
        amount=178.98,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Producer Invoice Seller: Best apples Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "logistics-1-wallet",
        amount=18.81,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Logistics Invoice Seller: Traidoo Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "global-platform-1-wallet",
        amount=9.71,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Credit Note Seller: Traidoo Buyer: Traidoo",
    )

    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "global-platform-1-wallet",
        amount=5.39,
        fees=1.08,
        tag=f"v2 Order: {order.id} Document: Platform Invoice Seller: Traidoo Buyer: Best apples",
    )

    assert mailoutbox[2].subject == "Fehler bei der Verarbeitung der Zahlung"
    assert (
        f"Cannot pay local platform owner his share 9.71 because "
        f"local platform owner `{platform_user.id}` does not have mangopay account. "
        f"Funds will be transfered to global platform owner"
    ) in mailoutbox[2].body
    assert set(mailoutbox[2].to) == set(get_admin_emails())


def test_mark_documents_and_invoice_as_paid_after_processing_payin(
    mangopay_bank_alias_payin,
    api_client,
    order,
    order_confirmation,
    producer_invoice,
    logistics_invoice,
    credit_note,
    platform_invoice,
    buyer_platform_invoice,
):

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    order.refresh_from_db()
    order_confirmation.refresh_from_db()
    producer_invoice.refresh_from_db()
    logistics_invoice.refresh_from_db()
    credit_note.refresh_from_db()
    buyer_platform_invoice.refresh_from_db()

    assert order.is_paid
    assert order_confirmation.paid
    assert logistics_invoice.paid
    assert producer_invoice.paid
    assert credit_note.paid
    assert buyer_platform_invoice.paid


def test_create_payouts_tasks_after_paying_invoices(
    mangopay_bank_alias_payin, send_task, api_client, order
):
    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    send_task.assert_any_call(
        "/mangopay/cron/payouts/10",
        queue_name="mangopay-payouts",
        http_method="POST",
        payload={"order_id": order.id, "amount": 178.98},
        headers={"Region": "traidoo", "Content-Type": "application/json"},
    )

    send_task.assert_any_call(
        "/mangopay/cron/payouts/30",
        queue_name="mangopay-payouts",
        http_method="POST",
        payload={"order_id": order.id, "amount": 18.81},
        headers={"Region": "traidoo", "Content-Type": "application/json"},
    )

    send_task.assert_any_call(
        "/mangopay/cron/payouts/40",
        queue_name="mangopay-payouts",
        http_method="POST",
        payload={"order_id": order.id, "amount": 9.71},
        headers={"Region": "traidoo", "Content-Type": "application/json"},
    )

    send_task.assert_any_call(
        "/mangopay/cron/payouts/50",
        queue_name="mangopay-payouts",
        http_method="POST",
        payload={
            "order_id": order.id,
            "amount": 4.31,
        },  # We can payout transfer value - mangopay fees
        headers={"Region": "traidoo", "Content-Type": "application/json"},
    )


def test_pay_in_for_order_confirmation_bankwire_pay_in_to_wallet(
    mangopay_wire_reference_payin,
    api_client,
    order,
    order_items,
    mailoutbox,
    order_confirmation,
    logistics_invoice,
    producer_invoice,
    platform_invoice,
    send_task,
    traidoo_region,
):
    # TODO Remove once all pay ins are migrated to banking alias payins

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    logistics_invoice.refresh_from_db()
    assert logistics_invoice.paid
    assert mailoutbox[1].to == [settings.LOGISTICS_EMAIL]
    assert mailoutbox[1].subject == f"Zahlung erhalten für Auftrag #{order.id}"
    assert (
        f"Wir haben folgenden Betrag erhalten EUR18.81 von ACME für den "
        f"Kauf # {order.id}."
    ) in mailoutbox[1].body

    platform_invoice.refresh_from_db()
    assert platform_invoice.paid
    assert mailoutbox[2].to == [settings.PLATFORM_EMAIL]
    assert mailoutbox[2].subject == (f"Zahlung erhalten für Auftrag #{order.id}")
    assert (
        f"Wir haben folgenden Betrag erhalten EUR16.18 von Best apples für "
        f"den Kauf # {order.id}."
    ) in mailoutbox[2].body

    producer_invoice.refresh_from_db()
    assert producer_invoice.paid
    assert mailoutbox[0].to == ["best@apples.de"]
    assert mailoutbox[0].subject == (f"Zahlung erhalten für Auftrag #{order.id}")
    assert (
        f"Wir haben folgenden Betrag erhalten EUR178.98 von ACME für "
        f"den Kauf # {order.id}."
    ) in mailoutbox[0].body

    order.refresh_from_db()
    order_confirmation.refresh_from_db()

    assert order.is_paid
    assert order_confirmation.paid
    assert send_task.call_args_list == [
        mock.call(
            "/mangopay/cron/payouts/10",
            http_method="POST",
            payload={"order_id": order.id, "amount": 178.98},
            queue_name="mangopay-payouts",
            headers={"Region": traidoo_region.slug, "Content-Type": "application/json"},
        ),
        mock.call(
            "/mangopay/cron/payouts/30",
            http_method="POST",
            payload={"order_id": order.id, "amount": 18.81},
            queue_name="mangopay-payouts",
            headers={"Region": traidoo_region.slug, "Content-Type": "application/json"},
        ),
        mock.call(
            "/mangopay/cron/payouts/40",
            http_method="POST",
            payload={"order_id": order.id, "amount": 9.71},
            queue_name="mangopay-payouts",
            headers={"Region": traidoo_region.slug, "Content-Type": "application/json"},
        ),
        mock.call(
            "/mangopay/cron/payouts/50",
            http_method="POST",
            payload={"order_id": order.id, "amount": 4.31},
            queue_name="mangopay-payouts",
            headers={"Region": traidoo_region.slug, "Content-Type": "application/json"},
        ),
    ]

    transfer = mangopay_wire_reference_payin.return_value.transfer
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "seller-1-wallet",
        amount=178.98,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Producer Invoice Seller: Best apples Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "logistics-1-wallet",
        amount=18.81,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Logistics Invoice Seller: Traidoo Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "global-platform-1-wallet",
        amount=5.39,
        fees=1.08,
        tag=f"v2 Order: {order.id} Document: Platform Invoice Seller: Traidoo Buyer: Best apples",
    )


def test_paid_too_much_bankwire_pay_in_to_wallet(
    mangopay_wire_reference_payin,
    order,
    order_items,
    mailoutbox,
    order_confirmation,
    logistics_invoice,
    producer_invoice,
    platform_invoice,
    api_client,
    admin,
):
    # Only applies to bankwire pay in to wallet
    # TODO Remove once all pay ins are migrated to banking alias pay ins

    mangopay_wire_reference_payin.return_value.get_pay_in.return_value = {
        "Status": "SUCCEEDED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR"},
        "DebitedFunds": {"Currency": "EUR", "Amount": 20033},
        "Fees": {"Currency": "EUR", "Amount": 593},
        "Id": "payin-1",
        "AuthorId": "mangopay-user-buyer",
    }

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    order.refresh_from_db()
    assert order.is_paid
    order_confirmation.refresh_from_db()
    assert order_confirmation.paid

    assert mailoutbox[0].subject == "Client paid too much"
    assert (
        f"Too much received in payin payin-1 for document "
        f"{order_confirmation.id}. Expected (in cents) `18088`, but received "
        f"`20033`\n"
    ) in mailoutbox[0].body
    assert set(mailoutbox[0].to) == set(get_admin_emails())


def test_seller_does_not_have_mangopay_user(
    mangopay_bank_alias_payin,
    api_client,
    mailoutbox,
    seller,
    order,
    order_items,
    order_confirmation,
    producer_invoice,
    platform_invoice,
    send_task,
    traidoo_region,
    central_platform_user,
):
    mangopay_user_id = seller.mangopay_user_id
    seller.mangopay_user_id = None
    seller.save()

    mangopay_bank_alias_payin.return_value.get_user_wallets.side_effect = [
        [{"Id": "logistics-1-wallet", "Currency": "EUR", "Description": "Default"}],
        [
            {
                "Id": "global-platform-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
                "Owners": [central_platform_user.mangopay_user_id],
            }
        ],
        [
            {
                "Id": "local-platform-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
            }
        ],
    ]

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    assert "Fehler bei der Verarbeitung der Zahlung" in mailoutbox[0].subject
    assert (
        f"Cannot process payin `payin-1`. Seller `{seller.id}` does not have mangopay account"
    ) in mailoutbox[0].body

    # Platform fee successfully transferred
    assert f"Zahlung erhalten für Auftrag #{order.id}" in mailoutbox[2].subject
    assert (
        f"Wir haben folgenden Betrag erhalten EUR16.18 von Best apples für "
        f"den Kauf # {order.id}."
    ) in mailoutbox[2].body

    producer_invoice.refresh_from_db()
    assert producer_invoice.paid is False

    transfer = mangopay_bank_alias_payin.return_value.transfer
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "logistics-1-wallet",
        amount=18.81,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Logistics Invoice Seller: Traidoo Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "global-platform-1-wallet",
        amount=5.39,
        fees=1.08,
        tag=f"v2 Order: {order.id} Document: Platform Invoice Seller: Traidoo Buyer: Best apples",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "local-platform-1-wallet",
        amount=9.71,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Credit Note Seller: Traidoo Buyer: Traidoo",
    )

    # TODO: do proper clean up
    seller.mangopay_user_id = mangopay_user_id
    seller.save()


def test_status_spoofed_in_webhook(mangopay, api_client, mailoutbox):

    mangopay.return_value.get_pay_in.return_value = {
        "Status": "FAILED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR", "Amount": 99},
        "Fees": {"Currency": "EUR", "Amount": 0},
        "Id": "payin-1",
        "AuthorId": "mangopay-user-buyer",
        "BankingAliasId": "234514543",
    }

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    assert "Fehler bei der Verarbeitung der Zahlung" in mailoutbox[-1].subject
    assert (
        "Successfully received payin-1 hook, but actual status is `failed`. "
        "Check with Mangopay details"
    ) in mailoutbox[-1].body


def test_not_enough_funds_on_debited_wallet(
    mangopay_bank_alias_payin,
    api_client,
    mailoutbox,
    order_items,
    order_confirmation,
    producer_invoice,
    platform_invoice,
    send_task,
):

    mangopay_bank_alias_payin.return_value.transfer.side_effect = MangopayTransferError(
        "Unsufficient wallet balance"
    )

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    assert "Fehler bei der Verarbeitung der Zahlung" == mailoutbox[0].subject
    assert (
        "Transfer from buyer wallet buyer-wallet-1 to seller wallet seller-1-wallet failed"
        in mailoutbox[0].body
    )
    assert "Mangopay error: Unsufficient wallet balance." in mailoutbox[0].body
    assert f"document {producer_invoice.id}" in mailoutbox[0].body
    assert not send_task.called


def test_payin_failed_webhook(mangopay, api_client, mailoutbox):

    mangopay.return_value.get_pay_in.return_value = {
        "Status": "FAILED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR", "Amount": 99},
        "Fees": {"Currency": "EUR", "Amount": 0},
        "Id": "payin-1",
        "AuthorId": "mangopay-user-buyer",
        "ResultMessage": "The payment has been refused",
        "BankingAliasId": "234514543",
    }

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_FAILED"},
    )

    assert "Fehler bei der Verarbeitung der Zahlung" in mailoutbox[0].subject
    assert (
        "Payin payin-1 failed. Error message: The payment has been refused. "
        "Check mangopay for further details."
    ) in mailoutbox[0].body


def test_paid_too_much_with_bank_alias(
    mangopay_bank_alias_payin,
    api_client,
    order,
    order_items,
    mailoutbox,
    order_confirmation,
    logistics_invoice,
    producer_invoice,
    platform_invoice,
):
    mangopay_bank_alias_payin.return_value.get_pay_in.return_value = {
        "Status": "SUCCEEDED",
        "CreditedWalletId": "buyer-wallet-1",
        "CreditedFunds": {"Currency": "EUR"},
        "DebitedFunds": {"Currency": "EUR", "Amount": 20033},
        "Fees": {"Currency": "EUR", "Amount": 593},
        "Id": "payin-1",
        "AuthorId": "mangopay-user-buyer",
        "CreditedUserId": "buyer-1",
        "BankingAliasId": "234514543",
    }
    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    order.refresh_from_db()
    assert order.is_paid
    order_confirmation.refresh_from_db()
    assert order_confirmation.paid

    assert mailoutbox[-1].subject == "User has extra cash in wallet"


def test_payout_succeeded(mangopay, api_client, mailoutbox, platform_user):
    mangopay.return_value.get_pay_out.return_value = {
        "Status": "SUCCEEDED",
        "CreditedFunds": {"Currency": "EUR", "Amount": 1000},
        "DebitedWalletId": "wallet-1",
        "AuthorId": platform_user.mangopay_user_id,
    }

    mangopay.return_value.get_wallet.return_value = {
        "Owners": [platform_user.mangopay_user_id]
    }

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "100", "EventType": "PAYOUT_NORMAL_SUCCEEDED"},
    )

    assert "EUR 10.00" in mailoutbox[-1].body


def test_ignore_payout_of_mangopay_fees(mangopay, api_client, mailoutbox):
    mangopay.return_value.get_pay_out.return_value = {
        "Status": "SUCCEEDED",
        "CreditedFunds": {"Currency": "EUR", "Amount": 1000},
        "DebitedWalletId": "FEES_EUR",
    }
    mangopay.return_value.get_wallet.side_effect = MangopayError(
        "Wallet not found"
    )  # make sure request would fail

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "100", "EventType": "PAYOUT_NORMAL_SUCCEEDED"},
    )

    assert len(mailoutbox) == 0


def test_payout_failed(mangopay, api_client, mailoutbox, platform_user):
    mangopay.return_value.get_pay_out.return_value = {
        "Status": "FAILED",
        "CreditedFunds": {"Currency": "EUR", "Amount": 1000},
        "DebitedWalletId": "wallet-1",
        "ResultMessage": "Failed for some reason",
        "AuthorId": platform_user.mangopay_user_id,
    }

    mangopay.return_value.get_wallet.return_value = {
        "Owners": [platform_user.mangopay_user_id]
    }

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "100", "EventType": "PAYOUT_NORMAL_FAILED"},
    )

    assert "EUR 10.00" in mailoutbox[-1].body
    assert "Failed for some reason" in mailoutbox[-1].body


def test_unexpected_exception_after_paying_for_producer(
    mangopay_bank_alias_payin,
    api_client,
    order,
    order_confirmation,
    producer_invoice,
    logistics_invoice,
    credit_note,
):

    mangopay_bank_alias_payin.return_value.transfer.side_effect = [
        {"Status": "SUCCEEDED"},
        MangopayError("Unexpected error"),
    ]

    with pytest.raises(MangopayError):
        api_client.get(
            reverse("webhook"),
            data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
        )

    producer_invoice.refresh_from_db()
    assert producer_invoice.paid
    logistics_invoice.refresh_from_db()
    assert logistics_invoice.paid is False
    order.refresh_from_db()
    assert order.is_paid is False
    credit_note.refresh_from_db()
    assert credit_note.paid is False


def test_exception_after_paying_for_logistics(
    mangopay_bank_alias_payin,
    api_client,
    order,
    order_confirmation,
    producer_invoice,
    logistics_invoice,
    credit_note,
):
    mangopay_bank_alias_payin.return_value.transfer.side_effect = [
        {"Status": "SUCCEEDED"},  # producer
        {"Status": "SUCCEEDED"},  # logistics
        MangopayError("Unexpected error"),
    ]

    with pytest.raises(MangopayError):
        api_client.get(
            reverse("webhook"),
            data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
        )

    credit_note.refresh_from_db()
    assert credit_note.paid is False

    producer_invoice.refresh_from_db()
    assert producer_invoice.paid

    logistics_invoice.refresh_from_db()
    assert logistics_invoice.paid

    order.refresh_from_db()
    assert order.is_paid is False


def test_exception_after_paying_for_credit_note_for_local_platform_owner(
    mangopay_bank_alias_payin,
    api_client,
    order,
    order_confirmation,
    producer_invoice,
    logistics_invoice,
    credit_note,
):
    mangopay_bank_alias_payin.return_value.transfer.side_effect = [
        {"Status": "SUCCEEDED"},  # producer
        {"Status": "SUCCEEDED"},  # logistics
        {"Status": "SUCCEEDED"},  # credit note to local platform
        MangopayError("Unexpected error"),
    ]

    with pytest.raises(MangopayError):
        api_client.get(
            reverse("webhook"),
            data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
        )

    credit_note.refresh_from_db()
    assert credit_note.paid

    producer_invoice.refresh_from_db()
    assert producer_invoice.paid

    logistics_invoice.refresh_from_db()
    assert logistics_invoice.paid

    order.refresh_from_db()
    assert order.is_paid is False


def test_do_not_try_pay_to_the_same_wallet(
    mangopay_bank_alias_payin, api_client, order, logistics_user, central_platform_user
):
    mangopay_bank_alias_payin.return_value.get_user_wallets.side_effect = [
        [
            {"Id": "buyer-wallet-1", "Currency": "EUR", "Description": "Default"}
        ],  # here we return same wallet for seller
        [
            {
                "Id": "logistics-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
                "Owners": [logistics_user.mangopay_user_id],
            }
        ],
        [
            {
                "Id": "global-platform-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
                "Owners": [central_platform_user.mangopay_user_id],
            }
        ],
        [
            {
                "Id": "local-platform-1-wallet",
                "Currency": "EUR",
                "Description": "Default",
            }
        ],
    ]

    api_client.get(
        reverse("webhook"),
        data={"RessourceId": "payin-1", "EventType": "PAYIN_NORMAL_SUCCEEDED"},
    )

    transfer = mangopay_bank_alias_payin.return_value.transfer

    assert transfer.call_count == 3

    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "logistics-1-wallet",
        amount=18.81,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Logistics Invoice Seller: Traidoo Buyer: ACME",
    )
    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "local-platform-1-wallet",
        amount=9.71,
        fees=0,
        tag=f"v2 Order: {order.id} Document: Credit Note Seller: Traidoo Buyer: Traidoo",
    )

    transfer.assert_any_call(
        "mangopay-buyer-1",
        "buyer-wallet-1",
        "global-platform-1-wallet",
        amount=5.39,
        fees=1.08,
        tag=f"v2 Order: {order.id} Document: Platform Invoice Seller: Traidoo Buyer: Best apples",
    )
