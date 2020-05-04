import pytest
from django.core.exceptions import ValidationError
from model_mommy import mommy

from settings.models import Setting


@pytest.mark.parametrize('central_share', (-1, 101))
def test_local_share_invalid_values(db, central_share):
    settings = mommy.make(Setting)
    settings.central_share = central_share

    with pytest.raises(ValidationError):
        settings.full_clean()
