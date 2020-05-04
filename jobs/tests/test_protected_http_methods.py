import pytest

pytestmark = pytest.mark.django_db


def test_http_create_job(client_buyer):
    response = client_buyer.post('/jobs')
    assert response.status_code == 405


def test_http_update_job(client_buyer):
    response = client_buyer.put('/jobs/1')
    assert response.status_code == 405

    response = client_buyer.patch('/jobs/1')
    assert response.status_code == 405


def test_http_delete_job(client_buyer):
    response = client_buyer.delete('/jobs/1')
    assert response.status_code == 405
