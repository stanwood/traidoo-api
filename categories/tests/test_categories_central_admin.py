from django.urls import reverse
from model_bakery import baker


def test_allow_change_container(central_platform_user, django_app):
    container = baker.make_recipe("categories.category")

    response = django_app.get(
        reverse("admin:categories_category_change", kwargs={"object_id": container.id}),
        user=central_platform_user,
    )
    assert len(response.form.fields) > 1


def test_allow_delete_container(central_platform_user, django_app):
    container = baker.make_recipe("containers.container")
    django_app.get(
        reverse("admin:categories_category_delete", kwargs={"object_id": container.id}),
        user=central_platform_user,
        status=302,
    )
