from rest_framework import serializers

from .models import Region


class RegionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Region
        fields = ("id", "name", "slug")
