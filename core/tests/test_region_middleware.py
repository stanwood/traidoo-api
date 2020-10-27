from rest_framework.test import APIClient


def test_skip_region_check_for_favicon():
    client = APIClient()
    response = client.get("/favicon.ico")
    assert response.status_code == 404
