import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_update_documents(
    buyer, client_buyer, storage, cloud_storage_save, cloud_storage_url, image_file
):
    assert not buyer.image
    assert not buyer.business_license

    business_license = SimpleUploadedFile(
        "file.pdf", b"file_content", content_type="application/pdf"
    )

    data = {"image": image_file, "business_license": business_license}
    response = client_buyer.put(f"/users/profile/documents", data, format="multipart")

    assert response.status_code == 200
    assert response.json()["businessLicense"].startswith(
        f"http://testserver/users/profile/private/user/{buyer.id}/"
    )
    assert response.json()["image"].startswith(
        f"http://testserver/users/profile/public/user/{buyer.id}/"
    )
    assert response.json()["image"].endswith(".png")
    assert response.json()["businessLicense"].endswith(".pdf")

    buyer.refresh_from_db()

    assert buyer.image.name.startswith(f"public/user/{buyer.id}/")
    assert buyer.image.name.endswith(".png")
    assert buyer.business_license.name.startswith(f"private/user/{buyer.id}/")
    assert buyer.business_license.name.endswith(".pdf")


@pytest.mark.django_db
def test_update_image(buyer, client_buyer, image_file):
    assert not buyer.image
    assert not buyer.business_license

    data = {"image": image_file}
    response = client_buyer.patch(f"/users/profile/documents", data, format="multipart")

    assert response.status_code == 200
    assert not response.json()["businessLicense"]
    assert response.json()["image"].startswith(
        f"http://testserver/users/profile/public/user/{buyer.id}/"
    )
    assert response.json()["image"].endswith(".png")

    buyer.refresh_from_db()

    assert buyer.image.name.startswith(f"public/user/{buyer.id}/")
    assert buyer.image.name.endswith(".png")
    assert not buyer.business_license
