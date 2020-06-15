from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, response, status
from rest_framework.permissions import AllowAny

from common.utils import get_region
from core.tasks.mixin import TasksMixin
from delivery_addresses.models import DeliveryAddress
from mails.utils import send_mail

from ..models.kyc import KycDocument
from ..serializers import RegistrationSerializer

User = get_user_model()


class RegistrationViewSet(generics.CreateAPIView, TasksMixin):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        region = get_region(request)

        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = serializer.validated_data
        user_password = user_data.pop("password")
        user_image = user_data.pop("image", None)
        user_business_license = user_data.pop("business_license")

        kyc_documents = {
            "identity_proof": KycDocument.Name.IDENTITY_PROOF.name,
            "shareholder_declaration": KycDocument.Name.SHAREHOLDER_DECLARATION.name,
            "articles_of_association": KycDocument.Name.ARTICLES_OF_ASSOCIATION.name,
            "registration_proof": KycDocument.Name.REGISTRATION_PROOF.name,
            "address_proof": KycDocument.Name.ADDRESS_PROOF.name,
        }

        documents_data = {key: user_data.pop(key, None) for key in kyc_documents.keys()}

        user = User.objects.create(**user_data, region=region)
        user.set_password(user_password)
        # Workaround to get instance ID in private_image_upload_to().
        if user_image:
            user.image = user_image
        user.business_license = user_business_license
        user.save()

        DeliveryAddress.objects.create(
            user=user,
            street=user.street,
            zip=user.zip,
            city=user.city,
            company_name=user.company_name,
        )

        for key, value in documents_data.items():
            if value:
                document = KycDocument.objects.create(
                    user=user, name=kyc_documents.get(key)
                )
                # Workaround to get instance ID in private_image_upload_to().
                document.file = value
                document.save()

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

        location = reverse("admin:users_user_changelist")

        send_mail(
            region=region,
            subject="Neuer Nutzer registriert",
            recipient_list=settings.REAL_ADMINS,
            template="mails/users/new_user_registered.html",
            context={
                "domain": self.request.get_host(),
                "location": location,
                "email": user.email,
            },
        )

        self.send_task(
            f"/users/{user.id}/mangopay/create",
            queue_name="mangopay-create-account",
            http_method="POST",
            schedule_time=10,
            headers={"Region": region.slug, "Content-Type": "application/json",},
        )

        return response.Response(status=status.HTTP_201_CREATED)
