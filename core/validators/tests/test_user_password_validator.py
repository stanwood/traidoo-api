import pytest
from django.core.exceptions import ValidationError

from ..user_password import UserPasswordValidator


@pytest.mark.parametrize(
    'password',
    [
        '',
        '1',
        '12345677889',
        'ascb23k23kk1231'
        'sjck123kasdn12321',
        'sjck123kasdn12321$',
        'sCk1$',
        'TestTest1234556789$$$'
    ],
)
@pytest.mark.django_db
def test_user_incorrect_password_format(password):
    with pytest.raises(ValidationError):
        UserPasswordValidator().validate(password)


@pytest.mark.parametrize(
    'password',
    [
        'Test1234$',
        'Test1234$$Test1234$',
    ],
)
@pytest.mark.django_db
def test_user_correct_password_format(password):
    UserPasswordValidator().validate(password)
