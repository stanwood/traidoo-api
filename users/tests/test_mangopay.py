from copy import copy

import pytest
from django.core.files.base import ContentFile

from users.models import KycDocument


@pytest.mark.django_db
def test_mangopay_kyc_documents_upload(
    seller, client_anonymous, send_task, mangopay, image_file
):
    mangopay.return_value.create_mangopay_natural_user.return_value = {"Id": 123}
    mangopay.return_value.create_mangopay_legal_user.return_value = {"Id": 123}

    document = KycDocument.objects.create(
        user=seller,
        name=KycDocument.Name.ARTICLES_OF_ASSOCIATION.name,
        file=ContentFile(image_file.read()),
    )

    response = client_anonymous.post(
        f"/users/{seller.id}/mangopay/create",
        **{"HTTP_X_APPENGINE_QUEUENAME": "documents"},
    )

    send_task.assert_called_once_with(
        f"/users/mangopay/documents/{document.id}",
        headers={"Region": seller.region.slug},
        http_method="POST",
        queue_name="documents",
        schedule_time=20,
    )
