from model_bakery.recipe import Recipe, foreign_key, related

from settings.baker_recipes import setting
from users.baker_recipes import user

from .models import Region

region = Recipe(
    Region, users=related(user), settings=related(setting)
)
