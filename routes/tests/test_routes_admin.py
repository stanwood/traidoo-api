from unittest import mock

import pytest
from django.urls import reverse
from model_bakery import baker


@pytest.fixture
def calculate_route_length():
    with mock.patch("routes.admin.Route.calculate_route_length") as mocked_method:
        yield mocked_method


def test_recalculate_route_length_after_changing_relevant_properties(
    calculate_route_length, django_app, admin
):
    route = baker.make_recipe("routes.route")
    form = django_app.get(
        reverse("admin:routes_route_change", kwargs={"object_id": route.id}),
        user=admin,
    ).form
    form.fields["waypoints"] = []
    form.submit()
    calculate_route_length.assert_called()


# Fix me: Bug in DynamicArray Field. 'has_changed' compares initial value in string format to array from form
@pytest.mark.skip("Fix me: DynamicArray has a bug in `has_changed` method.")
def test_do_not_recalculate_after_changing_frequency(
    calculate_route_length, django_app, admin
):
    route = baker.make_recipe("routes.route")
    form = django_app.get(
        reverse("admin:routes_route_change", kwargs={"object_id": route.id}),
        user=admin,
    ).form
    form.fields["frequency"] = [1]
    form.submit()
    calculate_route_length.assert_not_called()
