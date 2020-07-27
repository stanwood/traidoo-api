import datetime

from model_bakery.recipe import Recipe, foreign_key

from common.baker_recipes import region
from products.baker_recipes import product
from users.baker_recipes import user

from .models import Order, OrderItem

order = Recipe(
    Order,
    earliest_delivery_date=datetime.datetime.today(),
    region=foreign_key(region),
    buyer=foreign_key(user),
)
orderitem = Recipe(OrderItem, product=foreign_key(product))
