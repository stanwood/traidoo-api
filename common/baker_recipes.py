from model_bakery.recipe import Recipe, related

from settings.baker_recipes import setting

region = Recipe("common.Region", settings=related(setting))
