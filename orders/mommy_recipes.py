import datetime

from model_mommy.recipe import Recipe, foreign_key

from common.mommy_recipes import region
from products.mommy_recipes import product

from .models import Order, OrderItem

order = Recipe(
    Order, earliest_delivery_date=datetime.datetime.today(), region=foreign_key(region)
)
orderitem = Recipe(OrderItem, product=foreign_key(product))
