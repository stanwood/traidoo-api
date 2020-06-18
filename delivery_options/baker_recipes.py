from model_bakery.recipe import Recipe

from .models import DeliveryOption

central_logistic = Recipe(
    DeliveryOption, name="traidoo", id=DeliveryOption.CENTRAL_LOGISTICS
)
seller = Recipe(DeliveryOption, name="seller", id=DeliveryOption.SELLER)
buyer = Recipe(DeliveryOption, name="buyer", id=DeliveryOption.BUYER)
