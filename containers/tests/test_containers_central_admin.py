from django.urls import reverse
from model_bakery import baker


def test_allow_editing_containers(django_app, central_platform_user):
    container = baker.make_recipe("containers.container")

    response = django_app.get(
        reverse(
            "admin:containers_container_change", kwargs={"object_id": container.id}
        ),
        user=central_platform_user,
    )

    assert len(response.form.fields) > 1


def test_allow_deleting_containers(django_app, central_platform_user):
    container = baker.make_recipe("containers.container")

    django_app.get(
        reverse(
            "admin:containers_container_delete", kwargs={"object_id": container.id}
        ),
        user=central_platform_user,
        status=200,
    )
