from rest_framework import (
    generics,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from django.contrib.auth import get_user_model

from djoser.compat import get_user_email, get_user_email_field_name
from djoser.conf import settings

from djoser.utils import ActionViewMixin

User = get_user_model()

# TODO: https://github.com/sunscrapers/djoser/pull/340
# TODO: we need is_email_verified instead of is_active


class ResendActivationView(ActionViewMixin, generics.GenericAPIView):
    """
    Use this endpoint to resend user activation email.
    """
    serializer_class = settings.SERIALIZERS.password_reset
    permission_classes = [permissions.AllowAny]

    _users = None

    def _action(self, serializer):
        if not settings.SEND_ACTIVATION_EMAIL:
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        for user in self.get_users(serializer.data['email']):
            self.send_activation_email(user)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def get_users(self, email):
        if self._users is None:
            email_field_name = get_user_email_field_name(User)
            users = User._default_manager.filter(**{email_field_name + '__iexact': email})
            self._users = [u for u in users if not u.is_email_verified and u.has_usable_password()]
        return self._users

    def send_activation_email(self, user):
        context = {'user': user}
        to = [get_user_email(user)]
        settings.EMAIL.activation(self.request, context).send(to)
