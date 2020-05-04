import datetime

from faker import Faker
from model_mommy import mommy
from model_mommy.recipe import Recipe, foreign_key

from products.mommy_recipes import product

from .models import OrderItem, Order

order = Recipe(Order, earliest_delivery_date=datetime.datetime.today())
orderitem = Recipe(OrderItem, product=foreign_key(product))
