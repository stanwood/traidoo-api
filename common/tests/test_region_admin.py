from django.urls import reverse
from model_bakery import baker


def test_see_own_region_only(traidoo_region, platform_user, django_app):
    other_region = baker.make_recipe("common.region")
    response = django_app.get(
        reverse("admin:common_region_changelist"), user=platform_user
    )

    assert response.html.find("td", {"class": "field-name"}, text=traidoo_region.name)
    assert not response.html.find("td", {"class": "field-name"}, text=other_region.name)


def test_can_edit_own_region(traidoo_region, platform_user, django_app):
    other_region = baker.make_recipe("common.region")
    response = django_app.get(
        reverse("admin:common_region_change", kwargs={"object_id": traidoo_region.id}),
        user=platform_user,
    )
    assert len(response.form.fields) == 13

    response = django_app.get(
        reverse("admin:common_region_change", kwargs={"object_id": other_region.id}),
        user=platform_user,
    )

    assert response.status_code == 302


def test_superuser_can_add_region(django_app):
    superuser = baker.make_recipe("users.user", is_superuser=True, is_staff=True)
    response = django_app.get(reverse("admin:common_region_add"), user=superuser)
    assert response.status_code == 200


def test_superuser_can_delete_region(django_app, traidoo_region):
    superuser = baker.make_recipe("users.user", is_superuser=True, is_staff=True)
    response = django_app.get(
        reverse("admin:common_region_delete", kwargs={"object_id": traidoo_region.id}),
        user=superuser,
    )
    assert response.status_code == 200


def test_superuser_can_see_all_regions(django_app, admin_group):
    superuser = baker.make_recipe(
        "users.user", is_superuser=True, is_staff=True, groups=[admin_group]
    )
    response = django_app.get(reverse("admin:common_region_changelist"), user=superuser)
    assert len(response.html.find_all("th", attrs={"class": "field-id"})) == 3
