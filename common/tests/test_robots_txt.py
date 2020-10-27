from rest_framework.test import APIClient


def test_robots():
    client = APIClient()
    response = client.get("/robots.txt")
    assert response.status_code == 200
