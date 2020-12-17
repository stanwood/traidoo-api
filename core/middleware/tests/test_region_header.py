from rest_framework.test import APIClient


def test_missing_region_header():
    response = APIClient().get("/")
    assert response.status_code == 406
    assert response.json() == {
        "message": "Could not satisfy the request Region header.",
        "code": "not_acceptable",
    }
