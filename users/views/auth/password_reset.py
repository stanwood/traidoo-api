from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from mails.utils import send_mail
from users.serializers import EmailSerializer

User = get_user_model()


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = EmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=serializer.validated_data["email"])
        except User.DoesNotExist:
            pass
        else:
            send_mail(
                region=self.request.region,
                subject="Password reset",
                recipient_list=[user.email],
                template="mails/users/password_reset.html",
                context={
                    "domain": Site.objects.get_current().domain,
                    "url": f"password/reset/{user.generate_uid()}/{user.generate_token()}",
                },
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
