from faker import Faker
from model_mommy.recipe import Recipe, foreign_key, related

from common.mommy_recipes import region
from delivery_options.mommy_recipes import buyer, central_logistic, seller
from .models import Product

fake = Faker()


product = Recipe(
    Product,
    name=fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None),
    amount=fake.pydecimal(left_digits=2, right_digits=2, positive=True),
    price=fake.pydecimal(left_digits=2, right_digits=2, positive=True),
    vat=fake.pydecimal(left_digits=2, right_digits=2, positive=True),
    delivery_charge=fake.pydecimal(left_digits=2, right_digits=2, positive=True),
    region=foreign_key(region),
    delivery_options=related(buyer, central_logistic, seller),
)
