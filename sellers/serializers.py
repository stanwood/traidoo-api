from django.contrib.auth import get_user_model
from rest_framework import exceptions, serializers

from users.serializers.group import CustomGroupsSerializerField

User = get_user_model()


class SellerPublicSerializer(serializers.ModelSerializer):
    groups = CustomGroupsSerializerField(
        child=serializers.CharField(read_only=True), read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "description",
            "city",
            "image",
            "image_url",
            "groups",
        ]
