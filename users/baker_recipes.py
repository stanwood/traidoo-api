from faker import Faker
from model_bakery.recipe import Recipe


fake = Faker()


user = Recipe(
    "users.User",
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

staff_user = Recipe(
    "users.User",
    first_name=fake.first_name(),
    last_name=fake.last_name(),
    company_name=fake.company(),
    street=fake.street_address(),
    zip=fake.zipcode(),
    city=fake.city(),
    is_active=True,
    is_email_verified=True,
    phone="+00 123123123",
    is_staff=True,
)
