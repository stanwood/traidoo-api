import pytest
from model_bakery import baker

from overlays.models import Overlay


@pytest.mark.django_db
def test_get_all_overlays(client_anonymous):
    region_1 = baker.make_recipe("common.region", name="region-1", slug="region-1")
    region_2 = baker.make_recipe("common.region", name="region-2", slug="region-2")

    overlay_1 = baker.make_recipe(
        "overlays.overlay", overlay_type=Overlay.OVERLAY_TYPE_ANONYMOUS, region=region_1
    )
    overlay_2 = baker.make_recipe(
        "overlays.overlay",
        overlay_type=Overlay.OVERLAY_TYPE_NOT_COOPERATIVE,
        region=region_1,
    )
    overlay_3 = baker.make_recipe(
        "overlays.overlay",
        overlay_type=Overlay.OVERLAY_TYPE_NOT_VERIFIED,
        region=region_1,
    )
    overlay_4 = baker.make_recipe(
        "overlays.overlay",
        overlay_type=Overlay.OVERLAY_TYPE_NOT_VERIFIED,
        region=region_2,
    )

    response = client_anonymous.get("/overlays", **{"HTTP_REGION": region_1.slug},)
    response_json = response.json()
    response_json.sort(key=lambda overlay: overlay["overlayType"])

    assert response_json == [
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
    region = baker.make_recipe("common.region")
    overlay = baker.make_recipe(
        "overlays.overlay", overlay_type=Overlay.OVERLAY_TYPE_ANONYMOUS, region=region
    )

    overlay_button_2 = baker.make_recipe(
        "overlays.overlay_button", overlay=overlay, order=2
    )
    overlay_button_1 = baker.make_recipe(
        "overlays.overlay_button", overlay=overlay, order=1
    )
    overlay_button_3 = baker.make_recipe(
        "overlays.overlay_button", overlay=overlay, order=3
    )

    response = client_anonymous.get("/overlays", **{"HTTP_REGION": region.slug},)

    assert sorted(
        response.json()[0]["buttons"], key=lambda button: button["order"]
    ) == sorted(
        [
            {
                "title": overlay_button.title,
                "url": overlay_button.url,
                "order": overlay_button.order,
            }
            for overlay_button in {
                overlay_button_1,
                overlay_button_2,
                overlay_button_3,
            }
        ],
        key=lambda button: button["order"],
    )
