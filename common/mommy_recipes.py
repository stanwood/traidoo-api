from model_mommy.recipe import Recipe, foreign_key, related

from settings.mommy_recipes import setting

from .models import Region

region = Recipe(Region, settings=related(setting))
