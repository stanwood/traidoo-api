from faker import Faker
from model_mommy.recipe import Recipe, foreign_key

from .models import Setting

fake = Faker()


setting = Recipe(Setting, central_logistics_company=True)
