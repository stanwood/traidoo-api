from rest_framework import serializers

from settings.models import GlobalSetting, Setting


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ("min_purchase_value", "central_logistics_company")


class GlobalSettingSerializer(serializers.ModelSerializer):
    product_vat = serializers.ReadOnlyField()

    class Meta:
        model = GlobalSetting
        fields = ("product_vat",)
