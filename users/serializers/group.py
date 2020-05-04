import json
from json import JSONDecodeError

from rest_framework import serializers
from rest_framework.fields import empty


class CustomGroupsSerializerField(serializers.ListSerializer):
    def to_representation(self, value):
        if type(value) is not list:
            return [group.name for group in value.all()]
        return value

    def get_value(self, dictionary):
        value = dictionary.get(self.field_name, empty)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except JSONDecodeError:
                pass
        return value
