import pytest
from model_bakery import baker

from overlays.models import Overlay


@pytest.mark.django_db
def test_get_all_overlays(client_anonymous):
    overlay_1 = baker.make_recipe(
        "overlays.overlay", overlay_type=Overlay.OVERLAY_TYPE_ANONYMOUS
    )
    overlay_2 = baker.make_recipe(
        "overlays.overlay", overlay_type=Overlay.OVERLAY_TYPE_NOT_COOPERATIVE
    )
    overlay_3 = baker.make_recipe(
        "overlays.overlay", overlay_type=Overlay.OVERLAY_TYPE_NOT_VERIFIED
    )

    response = client_anonymous.get("/overlays")

    assert response.json() == [
        {
            "overlayType": overlay.overlay_type,
            "title": overlay.title,
            "subtitle": overlay.subtitle,
            "body": overlay.body,
            "avatar": f"http://testserver/{overlay.avatar.url}",
            "image": f"http://testserver/{overlay.image.url}",
            "buttons": [],
        }
        for overlay in (overlay_1, overlay_2, overlay_3)
    ]


@pytest.mark.django_db
def test_get_all_overlay_buttons(client_anonymous):
    overlay = baker.make_recipe(
        "overlays.overlay", overlay_type=Overlay.OVERLAY_TYPE_ANONYMOUS
    )

    overlay_button_1 = baker.make_recipe(
        "overlays.overlay_button", overlay=overlay, order=1
    )
    overlay_button_2 = baker.make_recipe(
        "overlays.overlay_button", overlay=overlay, order=2
    )
    overlay_button_3 = baker.make_recipe(
        "overlays.overlay_button", overlay=overlay, order=3
    )

    response = client_anonymous.get("/overlays")

    assert response.json() == [
        {
            "overlayType": overlay.overlay_type,
            "title": overlay.title,
            "subtitle": overlay.subtitle,
            "body": overlay.body,
            "avatar": f"http://testserver/{overlay.avatar.url}",
            "image": f"http://testserver/{overlay.image.url}",
            "buttons": [
                {
                    "title": overlay_button.title,
                    "url": overlay_button.url,
                    "order": overlay_button.order,
                }
                for overlay_button in {
                    overlay_button_3,
                    overlay_button_2,
                    overlay_button_1,
                }
            ],
        }
    ]
