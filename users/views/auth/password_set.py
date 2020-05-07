from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import get_region
from mails.utils import send_mail
from users.serializers import NewPasswordSerializer


class PasswordSetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = NewPasswordSerializer(data=request.data)
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
