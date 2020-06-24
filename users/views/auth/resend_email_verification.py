from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import get_region
from mails.utils import send_mail


class ResendEmailVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        region = get_region(request)
        user = self.request.user

        if not user.is_email_verified:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            send_mail(
                region=region,
                subject="Bitte bestätigen Sie Ihre E-Mail-Adresse",
                recipient_list=[user.email],
                template="mails/users/verify_email.html",
                context={
                    "domain": Site.objects.get_current().domain,
                    "url": f"registration/{uid}/{token}",
                },
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
