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
            "learnMoreUrl": overlay.learn_more_url,
            "avatar": f"http://testserver/{overlay.avatar.url}",
            "image": f"http://testserver/{overlay.image.url}",
        }
        for overlay in (overlay_1, overlay_2, overlay_3)
    ]
