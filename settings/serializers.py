from rest_framework import serializers

from settings.models import GlobalSetting, Setting


class SettingSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Setting
        fields = "__all__"


class GlobalSettingSerializer(serializers.ModelSerializer):
    product_vat = serializers.ReadOnlyField()

    class Meta:
        model = GlobalSetting
        fields = ("product_vat",)
