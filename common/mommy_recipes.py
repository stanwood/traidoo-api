from model_mommy.recipe import Recipe, related

from settings.mommy_recipes import setting
from users.mommy_recipes import user

from .models import Region

region = Recipe(Region, users=related(user), settings=related(setting))
