import itertools

from django.contrib.auth import get_user_model, password_validation
from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.constants.company_types import COMPANY_TYPES
from users.models.kyc import KycDocument

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):

    # Personal data

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    phone = serializers.CharField()
    password = serializers.CharField()
    birthday = serializers.DateField()
    nationality_country_code = CountryField()
    street = serializers.CharField()
    residence_country_code = serializers.CharField()
    city = serializers.CharField()
    zip = serializers.CharField()

    # Company data

    company_name = serializers.CharField()
    company_type = serializers.ChoiceField(
        choices=list(itertools.chain(*COMPANY_TYPES.values()))
    )
    iban = serializers.CharField(required=False)
    company_registration_id = serializers.CharField()
    vat_id = serializers.CharField(required=False)
    tax_id = serializers.CharField()
    is_certified_organic_producer = serializers.BooleanField(required=False)
    organic_control_body = serializers.CharField(required=False)
    declared_as_seller = serializers.BooleanField(required=False)

    # Documents

    business_license = serializers.FileField()
    image = serializers.FileField(required=False)

    # KYC Documents

    identity_proof = serializers.FileField(required=False)
    shareholder_declaration = serializers.FileField(required=False)
    articles_of_association = serializers.FileField(required=False)
    registration_proof = serializers.FileField(required=False)
    address_proof = serializers.FileField(required=False)

    def validate_password(self, value):
        password_validation.validate_password(value, self.instance)
        return value
