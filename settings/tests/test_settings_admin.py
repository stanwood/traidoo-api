from django.urls import reverse
from model_mommy import mommy


def test_see_own_settings_only(traidoo_settings, platform_user, django_app):
    other_settings = mommy.make_recipe("settings.setting")
    response = django_app.get(
        reverse("admin:settings_setting_changelist"), user=platform_user
    )

    assert response.html.find("th", {"class": "field-id"}, text=traidoo_settings.id)
    assert not response.html.find("th", {"class": "field-id"}, text=other_settings.id)


def test_can_edit_own_region(traidoo_settings, platform_user, django_app):
    other_settings = mommy.make_recipe("settings.setting")
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
