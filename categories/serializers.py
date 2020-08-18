from rest_framework import serializers

from categories.models import Category, CategoryIcon


class CategoryIconSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryIcon
        fields = ("id", "name", "icon_url")
        read_only_fields = ("id", "name", "icon_url")


class CategorySerializer(serializers.ModelSerializer):
    icon = CategoryIconSerializer()

    class Meta:
        model = Category
        fields = ("id", "icon", "name", "ordering", "default_vat", "parent")
        read_only_fields = ("id", "icon", "name", "ordering", "default_vat", "parent")
