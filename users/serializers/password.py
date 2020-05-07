from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework import serializers

from .token_uid import TokenUidSerializer


class NewPasswordSerializer(TokenUidSerializer):
    new_password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        super().validate(attrs)

        try:
            validate_password(attrs["new_password"])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs
