from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django_countries.serializers import CountryFieldMixin
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.serializers.image_fallback_mixin import ImageFallbackMixin

from .group import CustomGroupsSerializerField

User = get_user_model()


class AdminUserSerializer(CountryFieldMixin, ImageFallbackMixin, BaseUserSerializer):
    id = serializers.ReadOnlyField()
    groups = CustomGroupsSerializerField(child=serializers.CharField(), required=False)

    def update(self, instance, validated_data):

        try:
            validated_data["groups"]
        except KeyError:
            groups_names = None
        else:
            groups_names = validated_data.pop("groups", [])

        instance = super().update(instance, validated_data)

        if groups_names == None:
            return instance

        groups = []

        for group_name in groups_names:
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                raise ValidationError(f"Group {group_name} does not exist")
            else:
                groups.append(group)

        instance.groups.set(groups)

        return instance

    class Meta:
        model = User
        exclude = ("password", "user_permissions")
        image_fallback_fields = [
            ("image", "image_url"),
            ("id_photo", "id_photo_url"),
            ("business_license", "business_license_url"),
        ]
