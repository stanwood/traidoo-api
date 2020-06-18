from faker import Faker
from model_bakery.recipe import Recipe, foreign_key

from products.baker_recipes import product

from .models import Item

fake = Faker()

item = Recipe(
    Item,
    product=foreign_key(product),
    quantity=10,
    latest_delivery_date=fake.future_date(end_date="+2d", tzinfo=None),
)
