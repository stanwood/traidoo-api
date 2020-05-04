import pytest

from trucks.models import Truck


@pytest.mark.django_db
def test_count_trucks():
    Truck.objects.create(name='Truck 1')
    Truck.objects.create(name='Truck 2')

    trucks = Truck.objects.count()
    assert trucks == 2


@pytest.mark.django_db
def test_get_trucks_via_api(client_admin):
    Truck.objects.create(name='Truck 1')
    Truck.objects.create(name='Truck 2')

    response = client_admin.get('/trucks')

    parsed_response = response.json()

    assert len(parsed_response) == 2
