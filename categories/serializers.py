from rest_framework import serializers

from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ("id", "icon", "name", "ordering", "default_vat", "parent")
        read_only_fields = ("id", )
