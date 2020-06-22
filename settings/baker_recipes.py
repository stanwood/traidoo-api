from faker import Faker
from model_bakery.recipe import Recipe, foreign_key
from users.baker_recipes import staff_user

from .models import Setting

fake = Faker()

setting = Recipe(
    Setting, central_logistics_company=True, platform_user=foreign_key(staff_user)
)