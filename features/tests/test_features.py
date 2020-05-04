import pytest


@pytest.mark.django_db
def test_features_endpoint(client_anonymous, settings):
    settings.FEATURES['routes'] = False

    response = client_anonymous.get('/features')
    assert response.json()['routes'] is False
