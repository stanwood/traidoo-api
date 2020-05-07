import pytest


@pytest.mark.django_db
def test_get_token(client_anonymous, seller):
    user_password = "Test777*"
    seller.set_password(user_password)
    seller.save()

    response = client_anonymous.post(
        "/auth/token", {"email": seller.email, "password": user_password}
    )

    assert response.status_code == 200

    json_response = response.json()
    assert json_response["refresh"]
    assert json_response["access"]

@pytest.mark.django_db
def test_get_token_incorrect_email(client_anonymous):
    response = client_anonymous.post(
        "/auth/token", {"email":  'user@example.com', "password": 'test'}
    )

    assert response.status_code == 401
    assert response.json() == {'message': 'No active account found with the given credentials', 'code': 'no_active_account'}

@pytest.mark.django_db
def test_get_token_incorrect_password(client_anonymous, seller):
    response = client_anonymous.post(
        "/auth/token", {"email":  seller.email, "password": 'incorrect'}
    )

    assert response.status_code == 401
    assert response.json() == {'message': 'No active account found with the given credentials', 'code': 'no_active_account'}
