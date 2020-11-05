from faker import Faker
from model_bakery.recipe import Recipe, foreign_key

from users.baker_recipes import staff_user


fake = Faker()

setting = Recipe(
    "settings.Setting",
    central_logistics_company=True,
    platform_user=foreign_key(staff_user),
    deposit_vat=19,
    mc_swiss_delivery_fee_vat=19,
)

global_setting = Recipe("settings.GlobalSetting", product_vat=[0, 7, 11, 19])
