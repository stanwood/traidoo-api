import itertools
import re
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django_countries.fields import CountryField
from model_utils import FieldTracker

from common.models import Region
from core.db.base import BaseAbstractModel
from core.storage.private_storage import private_storage
from core.storage.utils import private_image_upload_to, public_image_upload_to
from core.tasks.mixin import TasksMixin
from mails.utils import send_mail
from settings.models import get_setting
from users.constants.company_types import COMPANY_TYPES

from .user_manager import UserManager


class User(TasksMixin, AbstractUser, BaseAbstractModel):
    username = None  # Remove AbstractUser.username

    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255)
    is_email_verified = models.BooleanField(default=False)

    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="users", blank=True, null=True
    )

    # Personal data
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birthday = models.DateField()
    phone = models.CharField(max_length=255)
    website = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    residence_country_code = CountryField()
    nationality_country_code = CountryField()

    invoice_email = models.EmailField(max_length=255, blank=True)

    tax_id = models.CharField(max_length=255, blank=True, null=True)
    bank = models.CharField(max_length=255, blank=True, null=True)
    bic = models.CharField(max_length=255, blank=True, null=True)

    mangopay_user_id = models.CharField(max_length=255, blank=True, null=True)
    mangopay_user_type = models.CharField(max_length=255, blank=True, null=True)
    mangopay_validation_level = models.CharField(
        max_length=255, blank=True, null=True, default="light"
    )

    # Comapny (seller) data
    image_url = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to=public_image_upload_to)

    business_license_url = models.CharField(max_length=255, blank=True, null=True)
    business_license = models.FileField(
        upload_to=private_image_upload_to,
        storage=private_storage,
        null=True,
        blank=True,
    )

    declared_as_seller = models.BooleanField(blank=True, null=True, default=False)

    company_name = models.CharField(max_length=255)
    company_type = models.CharField(
        max_length=255, choices=list(itertools.chain(*COMPANY_TYPES.values()))
    )

    vat_id = models.CharField(max_length=255, blank=True, null=True)
    iban = models.CharField(max_length=255, blank=True)
    company_registration_id = models.CharField(max_length=255, blank=True, null=True)
    association_registration_id = models.CharField(
        max_length=255, blank=True, null=True
    )
    organic_control_body = models.CharField(max_length=255, blank=True, null=True)
    is_certified_organic_producer = models.BooleanField(
        blank=True, null=True, default=False
    )

    is_cooperative_member = models.BooleanField(default=False)

    # Seller KYC documents
    id_photo_url = models.CharField(max_length=255, blank=True, null=True)
    id_photo = models.ImageField(  # identity_proof
        upload_to=private_image_upload_to,
        storage=private_storage,
        null=True,
        blank=True,
    )

    objects = UserManager()

    tracker = FieldTracker(fields=["is_active", "email"])

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "phone",
        "company_name",
        "birthday",
        "company_type",
        "street",
        "city",
        "zip",
        "residence_country_code",
        "nationality_country_code",
        "tax_id",
        "iban",
    ]

    def generate_uid(self):
        return urlsafe_base64_encode(force_bytes(self.pk))

    def generate_token(self):
        return default_token_generator.make_token(self)

    @property
    def is_seller(self) -> bool:
        return self.groups.filter(name="seller").exists()

    @property
    def is_admin(self) -> bool:
        return self.groups.filter(name="admin").exists()

    @property
    def is_buyer(self) -> bool:
        return self.groups.filter(name="buyer").exists()

    @property
    def approved(self):
        return (
            self.is_email_verified
            and self.groups.filter(name__in=["admin", "seller", "buyer"]).exists()
        )

    def get_all_email_addresses(self):
        return set(filter(None, [self.email, self.invoice_email]))

    @property
    def has_valid_iban(self):
        return re.match(r"[a-zA-Z]{2}\d{2}\s*(\w{4}\s*){2,7}\w{1,4}\s*$", self.iban)

    @property
    def address_as_str(self):
        return f"{self.company_name}, {self.street}, {self.zip}, {self.city}"

    @property
    def seller_platform_fee_rate(self):
        setting = get_setting(self.region.id)
        value = setting.charge

        if not self.is_cooperative_member:
            value += settings.NON_COOPERATIVE_MEMBERS_PLATFORM_FEE

        return value

    @property
    def buyer_platform_fee_rate(self):
        value = Decimal("0.0")

        if not self.is_cooperative_member:
            value += settings.NON_COOPERATIVE_MEMBERS_PLATFORM_FEE

        return value

    @classmethod
    def central_platform_user(cls):
        return cls.objects.get(email=settings.PLATFORM_EMAIL)


@receiver(post_save, sender=User)
def email_has_changed(sender, instance, created, **kwargs):
    # TODO: move it to view
    if created:
        return

    if instance.tracker.has_changed("email"):
        send_mail(
            region=instance.region,
            subject="Ihre E-Mail-Adresse wurde geändert",
            recipient_list=[instance.email],
            template="mails/users/email_change.html",
            context={
                "old_email": instance.tracker.previous("email"),
                "new_email": instance.email,
            },
        )
