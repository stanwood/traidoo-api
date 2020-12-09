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
from django.utils.functional import cached_property
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from model_utils import FieldTracker

from common.models import Region
from core.db.base import BaseAbstractModel
from core.storage.private_storage import private_storage
from core.storage.utils import private_image_upload_to, public_image_upload_to
from core.tasks.mixin import TasksMixin
from mails.utils import send_mail
from users.constants.company_types import COMPANY_TYPES

from .user_manager import UserManager


class User(TasksMixin, AbstractUser, BaseAbstractModel):
    username = None  # Remove AbstractUser.username

    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255, verbose_name=_("Password"))
    is_email_verified = models.BooleanField(
        default=False, verbose_name=_("Is email verified")
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="users",
        blank=True,
        null=True,
        verbose_name=_("Region"),
    )

    # Personal data
    first_name = models.CharField(max_length=255, verbose_name=_("First name"))
    last_name = models.CharField(max_length=255, verbose_name=_("Last name"))
    birthday = models.DateField(verbose_name=_("Birth date"))
    phone = models.CharField(max_length=255, verbose_name=_("Phone"))
    website = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Website")
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    street = models.CharField(max_length=255, verbose_name=_("Street"))
    city = models.CharField(max_length=255, verbose_name=_("City"))
    zip = models.CharField(max_length=255, verbose_name=_("Zip code"))
    residence_country_code = CountryField(verbose_name=_("Residence country code"))
    nationality_country_code = CountryField(verbose_name=_("Nationality country code"))

    invoice_email = models.EmailField(
        max_length=255, blank=True, verbose_name=_("Invoice email")
    )

    tax_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Tax id")
    )
    bank = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Bank name")
    )
    bic = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("BIC account number")
    )

    mangopay_user_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Mangopay user id")
    )
    mangopay_user_type = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Mangopay user type")
    )
    mangopay_validation_level = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="light",
        verbose_name=_("Mangopay validation level"),
    )

    # Comapny (seller) data
    image_url = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Image url")
    )
    image = models.ImageField(
        blank=True, null=True, upload_to=public_image_upload_to, verbose_name=_("Image")
    )

    business_license_url = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Business license url")
    )
    business_license = models.FileField(
        upload_to=private_image_upload_to,
        storage=private_storage,
        null=True,
        blank=True,
        verbose_name=_("Business license"),
    )

    declared_as_seller = models.BooleanField(
        blank=True, null=True, default=False, verbose_name=_("Declared as seller")
    )

    company_name = models.CharField(max_length=255, verbose_name=_("Company name"))
    company_type = models.CharField(
        max_length=255,
        choices=list(itertools.chain(*COMPANY_TYPES.values())),
        verbose_name=_("Company type"),
    )

    vat_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("VAT ID")
    )
    iban = models.CharField(max_length=255, blank=True, verbose_name=_("IBAN number"))
    company_registration_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Company registration id")
    )
    association_registration_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Association registration id"),
    )
    organic_control_body = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Organic control body")
    )
    is_certified_organic_producer = models.BooleanField(
        blank=True,
        null=True,
        default=False,
        verbose_name=_("Is certified organic producer"),
    )

    is_cooperative_member = models.BooleanField(
        default=False, verbose_name=_("Is cooperative member")
    )

    # Seller KYC documents
    id_photo_url = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Id photo url")
    )
    id_photo = models.ImageField(  # identity_proof
        upload_to=private_image_upload_to,
        storage=private_storage,
        null=True,
        blank=True,
        verbose_name=_("ID photo"),
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

    @cached_property
    def is_buyer_or_seller(self):
        return self.groups.filter(name__in=("seller", "buyer")).exists()

    @cached_property
    def is_seller(self) -> bool:
        return self.groups.filter(name="seller").exists()

    @property
    def is_admin(self) -> bool:
        return self.groups.filter(name="admin").exists()

    @cached_property
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

    @cached_property
    def setting(self):
        return self.region.settings.all()[0]

    @property
    def seller_platform_fee_rate(self):
        value = self.setting.charge

        if not self.is_cooperative_member:
            value += settings.NON_COOPERATIVE_MEMBERS_PLATFORM_FEE

        return value

    @cached_property
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
