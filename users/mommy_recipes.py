from django.contrib.auth.models import Group
from faker import Faker
from model_mommy.recipe import Recipe, seq

from .models import User

fake = Faker()


user = Recipe(
    User,
    first_name=fake.first_name(),
    last_name=fake.last_name(),
    company_name=fake.company(),
    street=fake.street_address(),
    zip=fake.zipcode(),
    city=fake.city(),
    is_active=True,
    is_email_verified=True,
    phone="+00 123123123",
)
