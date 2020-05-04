from unittest import mock

import pytest
from django.urls import reverse


@pytest.fixture
def mangopay_accepted_document(mangopay):
    mangopay.return_value.get_kyc_document.return_value = {
        "Status": "VALIDATED",
        "UserId": "10",
        "Type": "IDENTITY_PROOF",
    }
    mangopay.return_value.get_user.return_value = {"KYCLevel": "REGULAR"}
    yield mangopay


@pytest.fixture
def mangopay_rejected_document(mangopay):
    mangopay.return_value.get_kyc_document.return_value = {
        "Status": "REFUSED",
        "RefusedReasonType": "DOCUMENT_DO_NOT_MATCH_USER_DATA",
        "RefusedReasonMessage": "Wrong data",
        "UserId": "10",
        "Type": "IDENTITY_PROOF",
    }
    mangopay.return_value.get_user.return_value = {"KYCLevel": "LIGHT"}
    yield mangopay


def test_first_document_accepted(
    mangopay_accepted_document, api_client, mailoutbox, bucket, seller
):
    api_client.get(
        reverse("webhook"), data={"RessourceId": "100", "EventType": "KYC_SUCCEEDED"}
    )
    assert seller.mangopay_validation_level != "regular"
    assert len(mailoutbox) == 1
    assert mailoutbox[-1].to == [seller.email]
    assert (
        mailoutbox[-1].subject == "Account-Verfizierung wurde erfolgreich abgeschlossen"
    )
    assert "Personalausweis/Reisepass wurde akzeptiert." in mailoutbox[-1].body


def test_last_document_accepted(
    mangopay_accepted_document, api_client, seller, mailoutbox, bucket
):
    api_client.get(
        reverse("webhook"), data={"RessourceId": "100", "EventType": "KYC_SUCCEEDED"}
    )

    seller.refresh_from_db()
    assert seller.mangopay_validation_level == "regular"
    assert len(mailoutbox) == 1
    assert (
        mailoutbox[-1].subject == "Account-Verfizierung wurde erfolgreich abgeschlossen"
    )
    assert mailoutbox[-1].to == [seller.email]
    assert "Personalausweis/Reisepass wurde akzeptiert." in mailoutbox[-1].body
    assert "Ihr Bezahl-Account wurde freigeschaltet" in mailoutbox[-1].body


def test_document_rejected(
    mangopay_rejected_document, api_client, seller, mailoutbox, bucket
):
    api_client.get(
        reverse("webhook"), data={"RessourceId": "100", "EventType": "KYC_FAILED"}
    )

    assert len(mailoutbox) == 1
    assert mailoutbox[-1].subject == "Personalausweis/Reisepass wurde abgelehnt"
    assert mailoutbox[-1].to == [seller.email]
    assert "Personalausweis/Reisepass wurde abgelehnt." in mailoutbox[-1].body
    assert "Details: Wrong data" in mailoutbox[-1].body
