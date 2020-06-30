from faker import Faker
from model_bakery.recipe import Recipe

from .models import Route

fake = Faker()


route = Recipe(
    Route,
    origin=fake.address(),
    destination=fake.address(),
    frequency=[
        fake.pyint(min_value=1, max_value=7, step=1),
        fake.pyint(min_value=1, max_value=7, step=1),
        fake.pyint(min_value=1, max_value=7, step=1),
    ],
    length=fake.pyint(min_value=100, max_value=50000, step=1),
    waypoints=[fake.address(), fake.address(), fake.address()],
)
