from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserCompanyProfile(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "company_name",
            "company_type",
            "iban",
            "company_registration_id",
            "vat_id",
            "tax_id",
            "is_certified_organic_producer",
            "organic_control_body",
            "description",
            "zip",
            "street",
            "city"
        ]
