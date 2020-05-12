from django.urls import reverse
from model_mommy import mommy


def test_do_not_allow_change_container_local_admin(platform_user, django_app):
    container = mommy.make_recipe("containers.container")

    response = django_app.get(
        reverse(
            "admin:containers_container_change", kwargs={"object_id": container.id}
        ),
        user=platform_user,
    )
    assert len(response.form.fields) == 1


def test_do_not_allow_delete_container_by_local_admin(platform_user, django_app):
    container = mommy.make_recipe("containers.container")
    django_app.get(
        reverse(
            "admin:containers_container_delete", kwargs={"object_id": container.id}
        ),
        user=platform_user,
        status=403,
    )
