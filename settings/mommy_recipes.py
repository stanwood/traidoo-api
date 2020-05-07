from faker import Faker
from model_mommy.recipe import Recipe, foreign_key
from users.mommy_recipes import user

from .models import Setting

fake = Faker()

user = user.extend(is_staff=True)
setting = Recipe(Setting, central_logistics_company=True, platform_user=foreign_key(user))
