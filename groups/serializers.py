from django.contrib.auth.models import Group
from rest_framework import serializers


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = ('id', 'url', 'name')
