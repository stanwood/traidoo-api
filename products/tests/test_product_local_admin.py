from django.urls import reverse
from model_mommy import mommy


def test_allow_adding_products(django_app, platform_user):
    form = django_app.get(
        reverse("admin:products_product_add"), user=platform_user
    ).form

    assert len(form.fields) > 1
    assert "region" not in form.fields
    assert "seller" in form.fields
    assert "items-0-id" in form.fields


def test_allow_deleting_product(django_app, platform_user):
    product = mommy.make_recipe("products.product", region=platform_user.region)
    response = django_app.get(
        reverse("admin:products_product_delete", kwargs={"object_id": product.id}),
        user=platform_user,
    )

    assert response.html.find(text="Are you sure?")


def test_allow_edit_product_and_items(django_app, platform_user):
    product = mommy.make_recipe("products.product", region=platform_user.region)
    form = django_app.get(
        reverse("admin:products_product_change", kwargs={"object_id": product.id}),
        user=platform_user,
    ).form

    assert len(form.fields) > 1
    assert "region" not in form.fields
    assert "seller" in form.fields
    assert "items-0-id" in form.fields
