from model_mommy.recipe import Recipe, foreign_key, related

from settings.mommy_recipes import setting

from .models import DeliveryOption

central_logistic = Recipe(DeliveryOption, name="traidoo")
seller = Recipe(DeliveryOption, name="seller")
buyer = Recipe(DeliveryOption, name="buyer")
