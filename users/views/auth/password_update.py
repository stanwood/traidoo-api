from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from mails.utils import send_mail
from users.serializers import PasswordUpdateSerializer


class PasswordUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        serializer = PasswordUpdateSerializer(
            data=request.data, context={"user": request.user}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(serializer.data["new_password"])
        user.save()

        send_mail(
            region=request.region,
            subject="Ihr Password wurde geändert",
            recipient_list=[user.email],
            template="mails/users/password_change.html",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
