from django.contrib.auth import get_user_model
from rest_framework import serializers

from .group import CustomGroupsSerializerField

User = get_user_model()


class UserProfile(serializers.ModelSerializer):
    groups = CustomGroupsSerializerField(
        child=serializers.CharField(read_only=True), read_only=True
    )

    class Meta:
        model = User
        fields = ["id", "groups"]
        read_only_fields = ("id", "groups")
