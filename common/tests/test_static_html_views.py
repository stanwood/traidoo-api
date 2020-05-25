import pytest
from model_mommy import mommy


@pytest.mark.parametrize(
    "page_name",
    ["terms_of_services", "privacy_policy", "prices", "contact", "imprint"],
)
@pytest.mark.django_db
def test_region_static_sites(page_name, client_anonymous):
    region = mommy.make("common.region", **{page_name: f"<p>test {page_name}</p>"})

    response = client_anonymous.get(
        f"/regions/static/{page_name}", **{"HTTP_REGION": region.slug},
    )

    assert response.status_code == 200

    parsed_response = response.json()

    assert parsed_response == {"body": f"<p>test {page_name}</p>"}
