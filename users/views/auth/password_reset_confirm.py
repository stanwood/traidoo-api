from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import exceptions as django_exceptions
from django.template.loader import render_to_string
from loguru import logger
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import get_region
from mails.utils import send_mail

from .utils import decode_uid

User = get_user_model()


class PasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(style={"input_type": "password"})

    default_error_messages = {
        "invalid_token": "Invalid token for given user.",
        "invalid_uid": "Invalid user id or user doesn't exist.",
    }

    def __init__(self, *args, **kwargs):
        super(PasswordSerializer, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        logger.debug(f"Password reset validation: {attrs['uid']}")

        try:
            uid = decode_uid(attrs["uid"])
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            logger.debug(
                f"Password reset validation: {self.default_error_messages['invalid_uid']}"
            )
            raise serializers.ValidationError(
                {"uid": self.default_error_messages["invalid_uid"]}
            )

        logger.debug(f"Password reset validation: {self.user.id}")

        if not default_token_generator.check_token(self.user, attrs["token"]):
            logger.debug(
                f"Password reset validation: {self.default_error_messages['invalid_token']}"
            )
            raise serializers.ValidationError(
                {"token": self.default_error_messages["invalid_token"]}
            )

        try:
            validate_password(attrs["new_password"])
        except django_exceptions.ValidationError as e:
            logger.debug(f"Password reset validation: {list(e.messages)}")
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = PasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user
        user.set_password(serializer.data["new_password"])
        user.save()

        send_mail(
            region=get_region(request),
            subject="Ihr Password wurde geändert",
            recipient_list=[user.email],
            template="mails/users/password_change.html",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
