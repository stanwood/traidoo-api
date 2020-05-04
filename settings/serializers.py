from rest_framework import serializers

from settings.models import Setting


class SettingSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Setting
        fields = '__all__'
