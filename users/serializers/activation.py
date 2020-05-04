from djoser import constants
from djoser.serializers import UidAndTokenSerializer
from rest_framework import exceptions


class ActivationSerializer(UidAndTokenSerializer):
    default_error_messages = {"stale_token": constants.Messages.STALE_TOKEN_ERROR}

    def validate(self, attrs):
        attrs = super(ActivationSerializer, self).validate(attrs)
        if not self.user.is_email_verified:
            return attrs
        raise exceptions.PermissionDenied(self.error_messages["stale_token"])
