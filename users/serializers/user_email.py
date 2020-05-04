
from rest_framework import serializers


class UserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    user_id = serializers.IntegerField(required=False)
