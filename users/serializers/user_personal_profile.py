from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.serializers import RegionSerializer

User = get_user_model()


class UserPersonalProfile(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "invoice_email",
            "region",
            "birthday",
            "nationality_country_code",
            "phone",
            "residence_country_code",
        ]
