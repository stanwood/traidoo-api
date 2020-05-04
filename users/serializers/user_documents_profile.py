from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserDocumentsProfile(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["image", "business_license"]
