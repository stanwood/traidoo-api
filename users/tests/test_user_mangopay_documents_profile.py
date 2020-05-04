import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from payments.client.exceptions import MangopayError


@pytest.mark.django_db
def test_upload_mangopay_document(buyer, mangopay, client_buyer):
    buyer.mangopay_user_id = 123
    buyer.save()

    mangopay.create_kyc_document.return_value = {"Id": 123}

    pdf_file = SimpleUploadedFile(
        "file.pdf", b"file_content", content_type="application/pdf"
    )

    data = {"document_type": "IDENTITY_PROOF", "file": pdf_file}

    response = client_buyer.post(
        f"/users/profile/documents/mangopay", data, format="multipart"
    )

    assert mangopay.call_count == 3
    assert response.status_code == 204


@pytest.mark.django_db
def test_get_user_mangopay_documents(buyer, mangopay, client_buyer):
    mangopay.return_value.get_user_kyc_documents.return_value = [
        {
            "Type": "IDENTITY_PROOF",
            "UserId": "36518211",
            "Id": "54418238",
            "Tag": None,
            "CreationDate": 1_536_138_529,
            "ProcessedDate": None,
            "Status": "CREATED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "IDENTITY_PROOF",
            "UserId": "36518211",
            "Id": "54418366",
            "Tag": None,
            "CreationDate": 1_536_139_020,
            "ProcessedDate": None,
            "Status": "CREATED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "IDENTITY_PROOF",
            "UserId": "36518211",
            "Id": "54419982",
            "Tag": None,
            "CreationDate": 1_536_141_218,
            "ProcessedDate": 1_537_450_764,
            "Status": "VALIDATED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "REGISTRATION_PROOF",
            "UserId": "36518211",
            "Id": "54429411",
            "Tag": None,
            "CreationDate": 1_536_149_566,
            "ProcessedDate": 1_537_450_788,
            "Status": "VALIDATED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "IDENTITY_PROOF",
            "UserId": "36518211",
            "Id": "54434389",
            "Tag": None,
            "CreationDate": 1_536_152_630,
            "ProcessedDate": None,
            "Status": "VALIDATION_ASKED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "ARTICLES_OF_ASSOCIATION",
            "UserId": "36518211",
            "Id": "54437958",
            "Tag": None,
            "CreationDate": 1_536_155_187,
            "ProcessedDate": 1_536_245_401,
            "Status": "REFUSED",
            "RefusedReasonType": "DOCUMENT_UNREADABLE",
            "RefusedReasonMessage": None,
        },
        {
            "Type": "SHAREHOLDER_DECLARATION",
            "UserId": "36518211",
            "Id": "54495867",
            "Tag": None,
            "CreationDate": 1_536_247_851,
            "ProcessedDate": None,
            "Status": "VALIDATION_ASKED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "SHAREHOLDER_DECLARATION",
            "UserId": "36518211",
            "Id": "54496664",
            "Tag": None,
            "CreationDate": 1_536_248_099,
            "ProcessedDate": None,
            "Status": "VALIDATION_ASKED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
        {
            "Type": "REGISTRATION_PROOF",
            "UserId": "36518211",
            "Id": "54496761",
            "Tag": None,
            "CreationDate": 1_536_248_142,
            "ProcessedDate": 1_537_450_851,
            "Status": "VALIDATED",
            "RefusedReasonType": None,
            "RefusedReasonMessage": None,
        },
    ]

    expected_ids = ["54434389", "54437958", "54496664", "54496761"]

    response = client_buyer.get(f"/users/profile/documents/mangopay")

    assert set(expected_ids) == set([item["Id"] for item in response.json()])
    assert len(set([item["Type"] for item in response.json()])) == 4
    assert len([item["Type"] for item in response.json()]) == 4


@pytest.mark.django_db
def test_get_user_mangopay_documents_exception(buyer, mangopay, client_buyer):
    mangopay_error = {
        "Message": "The ressource does not exist",
        "Type": "ressource_not_found",
        "Id": "0ba799e1-722a-4eeb-bb7e-866b5a596d84#1553112804",
        "Date": 1_553_112_805.0,
        "errors": {
            "RessourceNotFound": "Cannot found the ressource User with the id=None "
        },
    }

    mangopay.return_value.get_user_kyc_documents.side_effect = MangopayError(
        json.dumps(mangopay_error).encode()
    )

    response = client_buyer.get(f"/users/profile/documents/mangopay")

    assert response.status_code == 400
    assert response.json()["message"] == mangopay_error["Message"]
