
from rest_framework import serializers

from users.models import KycDocument


class UserMangopayDocumentsSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=[document.name for document in KycDocument.Name])
    file = serializers.FileField()
