from model_bakery.recipe import Recipe

from categories.models import Category, CategoryIcon

category_icon = Recipe(CategoryIcon)
category = Recipe(Category)
