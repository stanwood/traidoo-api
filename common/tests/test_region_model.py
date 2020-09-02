import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_slug_should_be_generated_only_once():
    region = baker.make("common.region", id=100, name="Test Region 1", slug=None)
    assert region.slug == "test-region-1"

    region.name = "Test Region 2"
    region.save()
    assert region.slug == "test-region-1"
