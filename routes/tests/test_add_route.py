from unittest import mock

import pytest


@pytest.mark.django_db
def test_add_route_all_field_are_missing(seller, client_seller, send_task):
    response = client_seller.post("/routes")

    assert response.status_code == 400
    assert set(response.json().keys()) == set(["frequency", "origin", "destination"])
    assert [message[0] for message in response.json().values()] == [
        {"message": "This field is required.", "code": "required"},
        {"message": "This field is required.", "code": "required"},
        {"message": "This field is required.", "code": "required"},
    ]

    send_task.assert_not_called()


@pytest.mark.django_db
def test_add_frequency_field_cannot_be_empty(seller, client_seller, faker, send_task):
    origin = faker.address()
    destination = faker.address()
    waypoints = [faker.address(), faker.address()]
    response = client_seller.post(
        "/routes",
        {
            "frequency": [],
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints,
        },
    )

    assert response.status_code == 400
    assert set(response.json().keys()) == set(["frequency"])
    assert [message[0] for message in response.json().values()] == [
        {"message": "This list may not be empty.", "code": "empty"}
    ]

    send_task.assert_not_called()


@pytest.mark.django_db
@mock.patch("routes.models.calculate_route_length")
def test_add_route_success(
    calculate_route_length_mock, seller, client_seller, faker, send_task
):
    calculate_route_length_mock.return_value = 2222
    origin = faker.address()
    destination = faker.address()
    waypoints = [faker.address(), faker.address(), faker.address()]
    frequency = [1, 2, 3]

    response = client_seller.post(
        "/routes",
        {
            "frequency": frequency,
            "waypoints": waypoints,
            "origin": origin,
            "destination": destination,
        },
    )

    assert response.status_code == 201
    assert response.json()["waypoints"] == waypoints
    assert response.json()["frequency"] == frequency
    assert response.json()["origin"] == origin
    assert response.json()["destination"] == destination
    assert response.json()["length"] == 2222
    assert response.json()["createdAt"]
    assert response.json()["updatedAt"]
    assert response.json()["id"]

    calculate_route_length_mock.assert_called_once()

    assert (
        mock.call(
            f"/detours/create/{response.json()['id']}",
            http_method="POST",
            queue_name="routes",
            schedule_time=60,
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
@mock.patch("routes.models.calculate_route_length")
def test_add_route_success_without_waypoints(
    calculate_route_length_mock, seller, client_seller, faker, send_task
):
    calculate_route_length_mock.return_value = 1111
    origin = faker.address()
    destination = faker.address()
    waypoints = []
    frequency = [1, 2, 3]
    response = client_seller.post(
        "/routes",
        {
            "frequency": frequency,
            "waypoints": waypoints,
            "origin": origin,
            "destination": destination,
        },
    )

    assert response.status_code == 201
    assert response.json()["waypoints"] == waypoints
    assert response.json()["frequency"] == frequency
    assert response.json()["origin"] == origin
    assert response.json()["destination"] == destination
    assert response.json()["length"] == 1111
    assert response.json()["createdAt"]
    assert response.json()["updatedAt"]
    assert response.json()["id"]

    calculate_route_length_mock.assert_called_once()

    assert (
        mock.call(
            f"/detours/create/{response.json()['id']}",
            http_method="POST",
            queue_name="routes",
            schedule_time=60,
        )
        in send_task.call_args_list
    )


@pytest.mark.django_db
def test_add_route_incorrect_frequency_value(seller, client_seller, faker, send_task):
    origin = faker.address()
    destination = faker.address()
    waypoints = [faker.address(), faker.address(), faker.address()]
    frequency = [1, 2, 3, 8]
    response = client_seller.post(
        "/routes",
        {
            "frequency": frequency,
            "waypoints": waypoints,
            "origin": origin,
            "destination": destination,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "frequency": {
            "3": [{"message": '"8" is not a valid choice.', "code": "invalid_choice"}]
        }
    }

    send_task.assert_not_called()
