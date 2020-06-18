from django.urls import reverse
from model_bakery import baker


def test_do_not_allow_change_container_local_admin(platform_user, django_app):
    container = baker.make_recipe("categories.category")

    response = django_app.get(
        reverse("admin:categories_category_change", kwargs={"object_id": container.id}),
        user=platform_user,
    )
    assert len(response.form.fields) == 1


def test_do_not_allow_delete_container_by_local_admin(platform_user, django_app):
    container = baker.make_recipe("containers.container")
    django_app.get(
        reverse("admin:categories_category_delete", kwargs={"object_id": container.id}),
        user=platform_user,
        status=403,
    )
