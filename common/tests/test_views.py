import pytest
from model_mommy import mommy


@pytest.mark.django_db
def test_get_regions(client_buyer, neighbour_region):
    mommy.make("common.region", id=100, name="Test Region 1")
    mommy.make("common.region", id=101, name="Test Region 2")
    mommy.make("common.region", id=102, name="Test Region 3")

    response = client_buyer.get("/regions")

    assert response.status_code == 200

    parsed_response = response.json()

    assert parsed_response["results"] == [
        {"id": 1, "name": 'mcswiss', "slug": ''},
        {"id": neighbour_region.id, "name": "neighbour", "slug": "neighbour"},
        {"id": 100, "name": "Test Region 1", "slug": "test-region-1"},
        {"id": 101, "name": "Test Region 2", "slug": "test-region-2"},
        {"id": 102, "name": "Test Region 3", "slug": "test-region-3"},
    ]
