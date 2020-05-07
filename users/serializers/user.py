import itertools

from django.contrib.auth import get_user_model
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.serializers.image_fallback_mixin import ImageFallbackMixin
from users.constants.company_types import COMPANY_TYPES

from .group import CustomGroupsSerializerField

User = get_user_model()


class UserSerializer(CountryFieldMixin, ImageFallbackMixin):
    id = serializers.ReadOnlyField()

    groups = CustomGroupsSerializerField(
        child=serializers.CharField(read_only=True), read_only=True
    )

    class Meta:
        model = User
        exclude = ("password", "user_permissions")
        image_fallback_fields = [
            ("image", "image_url"),
            ("id_photo", "id_photo_url"),
            ("business_license", "business_license_url"),
        ]

    def validate(self, data):
        if self.context["request"].user.is_admin:
            return data

        company_types_except_natural_user = dict(COMPANY_TYPES)  # .pop('Natural')
        del company_types_except_natural_user["Natural"]
        company_types = list(
            itertools.chain(
                *list(itertools.chain(*company_types_except_natural_user.values()))
            )
        )

        if (
            self.context["request"].user.company_type in company_types
            and data.get("company_type") == "Einzelunternehmer"
        ):
            raise ValidationError(
                {"companyType": ["Change not allowed."]}  # TODO: Better error message?
            )

        return data
