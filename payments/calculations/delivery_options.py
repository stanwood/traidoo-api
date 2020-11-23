from carts.models import Cart
from common.models import Region
from decimal import Decimal
from delivery_options.models import DeliveryOption
from typing import Dict, List, Union


def calculate_delivery_options_prices(
    region: Region, cart: Cart
) -> List[Dict[str, Union[int, Decimal]]]:
    """
    Get the list of available delivery options for given item in the cart
    along with the prices.
    """

    region_settings = region.settings.first()

    delivery_options = []

    for product_delivery_option in cart.product.delivery_options.all():
        if product_delivery_option.id == DeliveryOption.BUYER:
            delivery_options.append(
                {"id": product_delivery_option.id, "value": Decimal("0.0")}
            )

        if product_delivery_option.id == DeliveryOption.SELLER:
            delivery_options.append(
                {
                    "id": product_delivery_option.id,
                    "value": cart.seller_delivery_fee.netto,
                }
            )

        if (
            product_delivery_option.id == DeliveryOption.CENTRAL_LOGISTICS
            and region_settings.central_logistics_company
        ):
            delivery_options.append(
                {
                    "id": DeliveryOption.CENTRAL_LOGISTICS,
                    "value": cart.central_logistic_delivery_fee.netto,
                }
            )

    return delivery_options
