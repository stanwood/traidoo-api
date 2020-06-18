from faker import Faker
from model_bakery.recipe import Recipe, foreign_key

from products.baker_recipes import product
from users.baker_recipes import user
from .models import Cart, CartItem


fake = Faker()


cart = Recipe(Cart, user=foreign_key(user))


cartitem = Recipe(
    CartItem,
    product=foreign_key(product),
    cart=foreign_key(cart),
    quantity=fake.pyint(min_value=0, max_value=20)
)
