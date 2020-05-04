import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UserPasswordValidator:
    def __init__(self, min_length=8):
        self.regex = re.compile(
            r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[a-zA-Z0-9!@#$%^&*()=-_+]{8,20}$'
        )

    def validate(self, password, user=None):
        if not self.regex.match(password):
            raise ValidationError(
                _('Incorrect password format.'), code='password_incorrect_format'
            )
