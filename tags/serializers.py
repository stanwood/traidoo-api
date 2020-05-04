from rest_framework import serializers

from taggit.models import Tag


class TagSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Tag
        fields = '__all__'
