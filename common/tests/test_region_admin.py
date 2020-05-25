from django.urls import reverse
from model_mommy import mommy


def test_see_own_region_only(traidoo_region, platform_user, django_app):
    other_region = mommy.make_recipe("common.region")
    response = django_app.get(
        reverse("admin:common_region_changelist"), user=platform_user
    )

    assert response.html.find("td", {"class": "field-name"}, text=traidoo_region.name)
    assert not response.html.find("td", {"class": "field-name"}, text=other_region.name)


def test_can_edit_own_region(traidoo_region, platform_user, django_app):
    other_region = mommy.make_recipe("common.region")
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
