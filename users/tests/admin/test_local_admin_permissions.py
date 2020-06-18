import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker


User = get_user_model()


@pytest.fixture
def user_from_traidoo(traidoo_region):
    yield baker.make_recipe("users.user", region=traidoo_region)


@pytest.fixture
def user_from_neighbour(neighbour_region):
    yield baker.make_recipe("users.user", region=neighbour_region)


def test_regional_admin_can_read_own_user_only(
    user_from_traidoo, user_from_neighbour, traidoo_region, django_app, platform_user
):

    response = django_app.get(
        reverse("admin:users_user_changelist"), user=platform_user
    )
    assert user_from_traidoo.email in response.testbody
    assert user_from_neighbour.email not in response.testbody


def test_regional_admin_can_write_own_users_only(
    traidoo_region,
    neighbour_region,
    user_from_neighbour,
    user_from_traidoo,
    django_app,
    platform_user,
):
    form = django_app.get(
        reverse("admin:users_user_change", kwargs={"object_id": user_from_traidoo.id}),
        user=platform_user,
    ).form
    form["first_name"] = "Foo"
    form.submit(user=platform_user)
    user_from_traidoo.refresh_from_db()
    assert user_from_traidoo.first_name == "Foo"

    response = django_app.get(
        reverse(
            "admin:users_user_change", kwargs={"object_id": user_from_neighbour.id}
        ),
        user=platform_user,
    )
    assert response.status_code == 302
    assert response.url == reverse("admin:index")


def test_regional_admin_can_delete_own_users_only(
    traidoo_region,
    neighbour_region,
    user_from_neighbour,
    user_from_traidoo,
    django_app,
    platform_user,
):
    response = django_app.get(
        reverse("admin:users_user_delete", kwargs={"object_id": user_from_traidoo.id}),
        user=platform_user,
    )
    assert response.status_code == 200
    assert "Are you sure?" in response.testbody
    response.form.submit()
    assert not User.objects.filter(id=user_from_traidoo.id).exists()

    response = django_app.get(
        reverse("admin:users_user_delete", kwargs={"object_id": user_from_neighbour.id})
    )
    assert response.status_code == 302
    assert response.url == reverse("admin:index")
    assert User.objects.filter(id=user_from_neighbour.id).exists()


def test_regional_addmin_cannot_add_users(traidoo_region, django_app, platform_user):
    django_app.get(reverse("admin:users_user_add"), user=platform_user, status=403)


def test_cannot_change_user_region(
    neighbour_region, user_from_traidoo, django_app, platform_user
):
    form = django_app.get(
        reverse("admin:users_user_change", kwargs={"object_id": user_from_traidoo.id}),
        user=platform_user,
    ).form
    assert "region" not in form.fields


def test_do_not_allow_change_to_super_user(
    user_from_traidoo, django_app, platform_user
):
    response = django_app.get(
        reverse("admin:users_user_change", kwargs={"object_id": user_from_traidoo.id}),
        user=platform_user,
    )
    assert "is_superuser" not in response.form.fields
