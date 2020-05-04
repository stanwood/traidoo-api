from unittest import mock

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import KycDocument


@pytest.mark.django_db
def test_kyc_documents_task(
    seller, client_anonymous, mangopay,
):
    document = KycDocument.objects.create(
        user=seller,
        name=KycDocument.Name.IDENTITY_PROOF.name,
        file=SimpleUploadedFile("file.pdf", b"file"),
    )

    response = client_anonymous.post(
        f"/users/mangopay/documents/{document.id}",
        **{"HTTP_X_APPENGINE_QUEUENAME": "queue"},
    )

    with pytest.raises(KycDocument.DoesNotExist):
        document.refresh_from_db()

    assert mangopay.call_count == 3
