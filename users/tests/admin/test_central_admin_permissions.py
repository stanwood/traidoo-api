from django.urls import reverse
from model_bakery import baker


def test_allow_set_superuser_flag(django_app, central_platform_user):
    new_admin = baker.make_recipe("users.user", is_superuser=False)
    response = django_app.get(
        reverse("admin:users_user_change", kwargs={"object_id": new_admin.id}),
        user=central_platform_user,
    )
    assert "is_superuser" in response.testbody
    response.form["is_superuser"].checked = True
    response.form.submit()
    new_admin.refresh_from_db()
    assert new_admin.is_superuser


def test_do_not_allow_creating_users(django_app, central_platform_user):
    django_app.get(
        reverse("admin:users_user_add"), user=central_platform_user, status=403
    )
