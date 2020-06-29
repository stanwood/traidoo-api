from django.urls import reverse
from model_bakery import baker


def test_see_own_settings_only(traidoo_settings, platform_user, django_app):
    other_settings = baker.make_recipe("settings.setting")
    response = django_app.get(
        reverse("admin:settings_setting_changelist"), user=platform_user
    )

    assert response.html.find("th", {"class": "field-id"}, text=traidoo_settings.id)
    assert not response.html.find("th", {"class": "field-id"}, text=other_settings.id)


def test_can_edit_own_region(traidoo_settings, platform_user, django_app):
    other_settings = baker.make_recipe("settings.setting")
    response = django_app.get(
        reverse(
            "admin:settings_setting_change", kwargs={"object_id": traidoo_settings.id}
        ),
        user=platform_user,
    )
    assert len(response.form.fields) == 15

    response = django_app.get(
        reverse(
            "admin:settings_setting_change", kwargs={"object_id": other_settings.id}
        ),
        user=platform_user,
    )

    assert response.status_code == 302


def test_superuser_can_add_setting(django_app):
    superuser = baker.make_recipe("users.user", is_superuser=True, is_staff=True)
    response = django_app.get(reverse("admin:settings_setting_add"), user=superuser)
    assert response.status_code == 200


def test_superuser_can_delete_setting(django_app, traidoo_settings):
    superuser = baker.make_recipe("users.user", is_superuser=True, is_staff=True)
    response = django_app.get(
        reverse(
            "admin:settings_setting_delete", kwargs={"object_id": traidoo_settings.id}
        ),
        user=superuser,
    )
    assert response.status_code == 200


def test_superuser_can_edit_region_of_setting(
    django_app, traidoo_settings, admin_group
):
    superuser = baker.make_recipe(
        "users.user", is_superuser=True, is_staff=True, groups=[admin_group]
    )
    region = baker.make_recipe("common.region")
    settings_form = django_app.get(
        reverse(
            "admin:settings_setting_change", kwargs={"object_id": traidoo_settings.id}
        ),
        user=superuser,
    ).form

    settings_form["region"].value = region.id
    settings_form.submit()

    traidoo_settings.refresh_from_db()
    assert traidoo_settings.region.id == region.id
