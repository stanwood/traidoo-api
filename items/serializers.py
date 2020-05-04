import pytz
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from core.serializers.image_fallback_mixin import ImageFallbackMixin
from items.models import Item
from products.models import Product


class _ProductSerializer(ImageFallbackMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'image', 'unit')


class ItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    product_id = serializers.IntegerField(write_only=True)
    product = _ProductSerializer(read_only=True)

    def validate(self, data):
        now = timezone.localtime(
            timezone.now(), pytz.timezone(settings.USER_DEFAULT_TIME_ZONE)
        )

        if data.get('latest_delivery_date') <= now.date():
            raise ValidationError(
                f"latest_delivery_date must greater than {now.date().strftime('%Y-%m-%d')}"
            )
        return data

    class Meta:
        model = Item
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=Item.objects.all(),
                fields=('product_id', 'latest_delivery_date'),
            )
        ]
