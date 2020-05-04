from faker import Faker
from model_mommy.recipe import Recipe

from .models import DeliveryAddress

fake = Faker()


delivery_address = Recipe(
    DeliveryAddress,
    company_name=fake.company(),
    street=fake.street_address(),
    zip=fake.zipcode(),
    city=fake.city(),
)
