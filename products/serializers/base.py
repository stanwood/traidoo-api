from rest_framework import serializers

from common.utils import get_region
from delivery_options.models import DeliveryOption
from delivery_options.serializers import DeliveryOptionSerializer
from products.models import Product


class BaseProductSerializer(serializers.Serializer):
    delivery_options = serializers.SerializerMethodField()

    def get_delivery_options(self, obj: Product):
        request = self.context.get("request")
        region = get_region(request)
        region_settings = region.settings.first()

        if region_settings.central_logistics_company:
            delivery_options = obj.delivery_options
        else:
            delivery_options = obj.delivery_options.exclude(
                id=DeliveryOption.CENTRAL_LOGISTICS
            )

        serialized_delivery_options = DeliveryOptionSerializer(
            delivery_options.order_by("id"), many=True
        )
        return serialized_delivery_options.data
