from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

User = get_user_model()


class TokenUidSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    default_error_messages = {
        "invalid_token": "Invalid token for given user.",
        "invalid_uid": "Invalid user id or user doesn't exist.",
    }

    def __init__(self, *args, **kwargs):
        super(TokenUidSerializer, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        try:
            uid = force_text(urlsafe_base64_decode((attrs["uid"])))
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError(
                {"uid": self.default_error_messages["invalid_uid"]}
            )

        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": self.default_error_messages["invalid_token"]}
            )

        return attrs
