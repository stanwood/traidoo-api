import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from faker import Faker

User = get_user_model()

fake = Faker()


class Command(BaseCommand):
    help = "Create test user"

    def add_arguments(self, parser):
        parser.add_argument("env", nargs="+", type=str)
        parser.add_argument("first_name", nargs="+", type=str)
        parser.add_argument("last_name", nargs="+", type=str)
        parser.add_argument("email", nargs="+", type=str)
        parser.add_argument("password", nargs="+", type=str)

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.ERROR(
                "Are you sure? This command should not be used on production!"
            )
        )
        raise SystemExit

        username, domain = options["email"][0].split("@")

        superadmin_email = f"{username}+{options['env'][0]}@{domain}"
        admin_email = f"{username}+admin-{options['env'][0]}@{domain}"
        seller_email = f"{username}+seller-{options['env'][0]}@{domain}"
        buyer_email = f"{username}+buyer-{options['env'][0]}@{domain}"

        self._create_user(
            "superuser",
            options["first_name"][0],
            options["last_name"][0],
            superadmin_email,
            options["password"][0],
        )

        self._create_user(
            "admin",
            options["first_name"][0],
            options["last_name"][0],
            admin_email,
            options["password"][0],
        )

        self._create_user(
            "seller",
            options["first_name"][0],
            options["last_name"][0],
            seller_email,
            options["password"][0],
        )

        self._create_user(
            "buyer",
            options["first_name"][0],
            options["last_name"][0],
            buyer_email,
            options["password"][0],
        )

    def _create_user(self, user_type, first_name, last_name, email, password):
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=first_name,
            phone=fake.phone_number(),
            company_name=fake.company(),
            birthday=datetime.datetime.utcnow().date(),
            company_type="Einzelunternehmer",
            street=fake.street_address(),
            city=fake.city(),
            zip=fake.zipcode(),
            residence_country_code="DE",
            nationality_country_code="DE",
            tax_id=fake.itin(),
            id_photo_url="https://storage.example.com/test.pdf",
            business_license_url="https://storage.example.com/test.pdf",
        )

        user.is_active = True
        user.is_email_verified = True

        if user_type == "superuser":
            user.is_superuser = True
            user.is_staff = True

        user.save()

        if user_type != "superuser":
            group = Group.objects.get(name=user_type)
            group.user_set.add(user)
