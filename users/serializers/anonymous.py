from django.contrib.auth import get_user_model
from django_countries.serializers import CountryFieldMixin
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from core.serializers.image_fallback_mixin import ImageFallbackMixin

User = get_user_model()


class AnonymousUserSerializer(
    CountryFieldMixin, ImageFallbackMixin, BaseUserSerializer
):
    id = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "description",
            "city",
            "image",
            "company_name",
        )
        image_fallback_fields = [
            ("image", "image_url"),
            ("id_photo", "id_photo_url"),
            ("business_license", "business_license_url"),
        ]
