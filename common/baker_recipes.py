from model_bakery.recipe import Recipe, related

from settings.baker_recipes import setting

from .models import Region

region = Recipe(Region, settings=related(setting))
