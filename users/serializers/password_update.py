from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework import serializers

from .token_uid import TokenUidSerializer


class PasswordUpdateSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    re_new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError(
                {"current_password": "The two password fields didn't match."}
            )

        try:
            validate_password(attrs["new_password"], self.context["user"])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        if not self.context["user"].check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Invalid password."})

        return attrs
