from django.urls import reverse
from model_mommy import mommy


def test_local_admin_view_orders(django_app, platform_user):
    order = mommy.make_recipe("orders.order", region=platform_user.region)
    other_order = mommy.make_recipe("orders.order")

    response = django_app.get(
        reverse("admin:orders_order_changelist"), user=platform_user
    )
    assert response.html.find("td", {"class": "field-id"}, text=order.id)
    assert response.html.find("td", {"class": "field-id"}, text=other_order.id) is None


def test_local_admin_cannot_edit_order(django_app, platform_user):
    order = mommy.make_recipe("orders.order", region=platform_user.region)
    response = django_app.get(
        reverse("admin:orders_order_change", kwargs={"object_id": order.id}),
        user=platform_user,
    )

    assert len(response.form.fields) == 9  # only formset hidden fields
    for _, field in response.form.fields.items():
        assert field[0].attrs["type"] == "hidden"


def test_local_admin_cannot_delete_order(django_app, platform_user):
    order = mommy.make_recipe("orders.order", region=platform_user.region)
    django_app.get(
        reverse("admin:orders_order_delete", kwargs={"object_id": order.id}),
        user=platform_user,
        status=403,
    )
