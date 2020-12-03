import pytz
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from items.models import Item
from products.models import Product


class ItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate(self, data):
        now = timezone.localtime(
            timezone.now(), pytz.timezone(settings.USER_DEFAULT_TIME_ZONE)
        )

        if data.get("latest_delivery_date") <= now.date():
            raise ValidationError(
                f"latest_delivery_date must greater than {now.date().strftime('%Y-%m-%d')}"
            )

        return data

    class Meta:
        model = Item
        fields = "__all__"

        validators = [
            UniqueTogetherValidator(
                queryset=Item.objects.all(),
                fields=("product", "latest_delivery_date"),
            )
        ]
